"""Ensaio da EXECUÇÃO com um robô falso, num contêiner SEM REDE. Não toca o robô real.

O robô falso tem os servidores de navegação, dock e saída da doca, o estado da doca, a bateria
e a transformação map->odom; o Ollama também é falso. O nó é o de verdade, com o freio
desligado. Rodar na raiz do repositório (leva alguns minutos):

    docker run --rm --network none -e COMPILAR_WS=patrulha_tb4,llm_tb4 -e ROS_DOMAIN_ID=43 \
        -e ROS_LOCALHOST_ONLY=1 -v "$PWD/workspace:/workspace:ro" \
        -v "$PWD/workspace/mapas:/mapas:ro" physical-ai:base \
        python3 /workspace/meu_ws/src/llm_tb4/test/ensaio_execucao.py
"""
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import rclpy
from geometry_msgs.msg import TransformStamped
from irobot_create_msgs.action import Dock, Undock
from irobot_create_msgs.msg import DockStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient, ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, String
from tf2_msgs.msg import TFMessage

from llm_tb4 import pontos

DOCA, PONTOS = pontos.ler_pontos(pontos.ARQUIVO_PADRAO)
registro, falhas = [], []
atraso_modelo = [0.1]


class OllamaFalso(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        frase = corpo['messages'][1]['content']
        time.sleep(atraso_modelo[0])
        acao, local = 'nenhuma', 'nenhum'
        for palavra, escolhido in (('ponto 4', 'ponto_4'), ('geladeira', 'ponto_2'),
                                   ('porta', 'ponto_3')):
            if palavra in frase:
                acao, local = 'ir_para', escolhido
        if 'volte' in frase:
            acao = 'voltar_para_base'
        if ' x ' in frase:
            acao = 'ir_para_coordenadas'
        saida = json.dumps({'message': {'content': json.dumps(
            {'acao': acao, 'local': local})}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(saida)

    def log_message(self, *args):
        pass


class RoboFalso(Node):
    def __init__(self):
        super().__init__('robo_falso', namespace='/robot1')
        grupo = ReentrantCallbackGroup()
        self.trava = threading.Lock()
        self.eventos = []            # (instante, 'inicio'|'cancelar'|'fim', tipo, detalhe)
        self.ativas = self.maximo_ativas = 0
        self.pronto = []
        self.reiniciar()
        for tipo, classe, nome in (('navegar', NavigateToPose, 'navigate_to_pose'),
                                   ('encaixar', Dock, 'dock'), ('sair', Undock, 'undock')):
            ActionServer(
                self, classe, nome,
                execute_callback=lambda meta, t=tipo, c=classe: self.executar(meta, t, c),
                goal_callback=lambda _meta: (GoalResponse.REJECT if self.recusar
                                             else GoalResponse.ACCEPT),
                cancel_callback=lambda _meta, t=tipo: self.ao_cancelar(t), callback_group=grupo)
        self.pub_doca = self.create_publisher(DockStatus, 'dock_status', qos_profile_sensor_data)
        self.pub_bateria = self.create_publisher(BatteryState, 'battery_state',
                                                 qos_profile_sensor_data)
        self.pub_tf = self.create_publisher(TFMessage, 'tf', 100)
        self.pub_pedido = self.create_publisher(String, 'user_input', 10)
        self.create_subscription(Bool, 'ready_for_input',
                                 lambda m: self.pronto.append(m.data), 10,
                                 callback_group=grupo)
        self.create_timer(0.2, self.publicar, callback_group=grupo)

    def reiniciar(self):
        self.na_doca, self.doca_visivel, self.bateria, self.tf = False, True, 0.9, True
        self.duracao = {'navegar': 1.0, 'sair': 1.0, 'encaixar': 1.0}
        self.recusar = self.ignorar_cancelamento = False

    def publicar(self):
        self.pub_doca.publish(DockStatus(is_docked=self.na_doca, dock_visible=self.doca_visivel))
        self.pub_bateria.publish(BatteryState(percentage=self.bateria))
        if self.tf:
            t = TransformStamped()
            t.header.frame_id, t.child_frame_id = 'map', 'odom'
            self.pub_tf.publish(TFMessage(transforms=[t]))

    def anotar(self, oque, tipo, detalhe=None):
        self.eventos.append((time.monotonic(), oque, tipo, detalhe))

    def ao_cancelar(self, tipo):
        self.anotar('cancelar', tipo)
        return CancelResponse.REJECT if self.ignorar_cancelamento else CancelResponse.ACCEPT

    def executar(self, meta, tipo, classe):
        detalhe = None
        if tipo == 'navegar':
            p = meta.request.pose.pose.position
            detalhe = (round(p.x, 3), round(p.y, 3))
        with self.trava:
            self.ativas += 1
            self.maximo_ativas = max(self.maximo_ativas, self.ativas)
        self.anotar('inicio', tipo, detalhe)
        inicio = time.monotonic()
        resultado = 'sucesso'
        while time.monotonic() - inicio < self.duracao[tipo]:
            if meta.is_cancel_requested:
                resultado = 'cancelada'
                break
            time.sleep(0.02)
        with self.trava:
            self.ativas -= 1
        self.anotar('fim', tipo, resultado)
        if resultado == 'cancelada':
            meta.canceled()
        else:
            if tipo != 'navegar':
                self.na_doca = tipo == 'encaixar'
            meta.succeed()
        return classe.Result()


def subir(*argumentos):
    processo = subprocess.Popen(
        ['ros2', 'launch', 'llm_tb4', 'natural_language_nav_launch.py', 'namespace:=/robot1',
         'ollama_url:=http://127.0.0.1:18081/api/chat', *argumentos], stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, start_new_session=True)
    threading.Thread(target=lambda: [registro.append(linha.rstrip()) for linha in processo.stdout],
                     daemon=True).start()
    return processo


def encerrar(processo, sinal=signal.SIGINT):
    if processo.poll() is None:
        os.killpg(processo.pid, sinal)
        try:
            processo.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(processo.pid, signal.SIGKILL)


def conferir(nome, condicao):
    print('OK    ' if condicao else 'FALHOU', nome, flush=True)
    if not condicao:
        falhas.append(nome)
        print('\n'.join(registro[-12:]), flush=True)


def esperar(condicao, limite=10):
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        if condicao():
            return True
        time.sleep(0.02)
    return False


def achou(*partes):
    return any(all(parte in linha for parte in partes) for linha in registro)


def main():
    servidor = ThreadingHTTPServer(('127.0.0.1', 18081), OllamaFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    rclpy.init()
    robo = RoboFalso()
    executor = MultiThreadedExecutor(num_threads=8)
    executor.add_node(robo)
    threading.Thread(target=executor.spin, daemon=True).start()

    def inicios(tipo=None):
        return [e for e in robo.eventos if e[1] == 'inicio' and tipo in (None, e[2])]

    def fins(tipo=None):
        return [e for e in robo.eventos if e[1] == 'fim' and tipo in (None, e[2])]

    def dizer(texto):
        robo.pub_pedido.publish(String(data=texto))
        return time.monotonic()

    def preparar(**estado):
        """Leva o nó ao repouso, zera os registros e arruma o robô falso."""
        robo.ignorar_cancelamento = False
        dizer('pare')            # encerra qualquer missão anterior, inclusive passos por vir
        time.sleep(0.5)
        esperar(lambda: robo.ativas == 0, 40)
        esperar(lambda: robo.pronto[-1:] != [False], 10)
        robo.reiniciar()
        for nome, valor in estado.items():
            if nome in robo.duracao:
                robo.duracao[nome] = valor
            else:
                setattr(robo, nome, valor)
        time.sleep(1.0)          # o nó recebe o novo estado dos sensores
        robo.eventos.clear()
        registro.clear()
        robo.maximo_ativas = 0

    def navegando(frase='vá ao ponto 4', **estado):
        preparar(navegar=30.0, **estado)
        dizer(frase)
        return esperar(lambda: inicios('navegar'), 10)

    def cancelada_depressa(instante, tipo='navegar'):
        ok = esperar(lambda: [e for e in fins(tipo) if e[3] == 'cancelada'], 3)
        return ok and fins(tipo)[-1][0] - instante < 1.0

    processo = subir('parking_brake:=false')
    conferir('sobe com o freio desligado e avisa', esperar(
        lambda: achou('FREIO DESLIGADO') and robo.pronto[-1:] == [True], 40))

    # ---------------------------------------------------------- missões
    preparar(na_doca=True)
    dizer('vá ao ponto 4')
    conferir('na doca: sai, confirma e navega até o ponto 4', esperar(
        lambda: achou('CONCLUIDO'), 15)
        and [e[2] for e in inicios()] == ['sair', 'navegar']
        and inicios('navegar')[0][3] == tuple(round(v, 3) for v in PONTOS[3]))

    preparar()
    dizer('volte para a doca')
    conferir('voltar: aproxima no ponto 1 e encaixa', esperar(
        lambda: achou('CONCLUIDO'), 15)
        and [e[2] for e in inicios()] == ['navegar', 'encaixar'] and robo.na_doca
        and inicios('navegar')[0][3] == tuple(round(v, 3) for v in PONTOS[0]))

    preparar()
    dizer('vá para x -3.55 y -3.063')
    conferir('coordenada livre é enviada como pedida', esperar(
        lambda: inicios('navegar') and inicios('navegar')[0][3] == (-3.55, -3.063), 10))
    preparar()
    dizer('vá para x 100 y 100')
    time.sleep(2)
    dizer('vá para x -0.3 y 0.1')
    time.sleep(2)
    conferir('fora do mapa e junto da doca: nada é enviado',
             not inicios() and achou('fora_do_mapa') and achou('perto_da_doca'))

    # ---------------------------------------------------------- interrupções
    conferir('começa a navegar', navegando())
    t = dizer('vá para a geladeira')
    conferir('mensagem no trajeto cancela em menos de 1 s', cancelada_depressa(t))
    conferir('e vira a ordem principal', esperar(
        lambda: len(inicios('navegar')) == 2
        and inicios('navegar')[1][3] == tuple(round(v, 3) for v in PONTOS[1]), 10))
    conferir('nunca há duas metas ao mesmo tempo', robo.maximo_ativas == 1)

    t = dizer('pare')
    conferir('"pare" cancela em menos de 1 s', cancelada_depressa(t))
    time.sleep(2)
    conferir('depois do "pare" nada novo é enviado', len(inicios()) == 2)

    navegando()
    t = dizer('eita')
    conferir('mensagem que não é comando também cancela', cancelada_depressa(t))
    time.sleep(2)
    conferir('e o robô fica parado', len(inicios()) == 1)

    navegando()
    atraso_modelo[0] = 3.0
    t = dizer('vá para a porta')
    conferir('cancela antes de o modelo responder', cancelada_depressa(t))
    dizer('vá para a geladeira')
    conferir('duas mensagens seguidas: vale a última', esperar(
        lambda: len(inicios('navegar')) == 2
        and inicios('navegar')[1][3] == tuple(round(v, 3) for v in PONTOS[1]), 15)
        and achou('DESCARTADO'))
    atraso_modelo[0] = 0.1
    dizer('pare')

    # ---------------------------------------------------------- dock e saída
    preparar(na_doca=True, sair=4.0, navegar=30.0)
    dizer('vá ao ponto 4')
    esperar(lambda: inicios('sair'), 10)
    dizer('vá para a geladeira')
    conferir('na saída da doca a manobra termina', esperar(lambda: fins('sair'), 10)
             and fins('sair')[0][3] == 'sucesso')
    conferir('e a última mensagem é obedecida', esperar(
        lambda: inicios('navegar')
        and inicios('navegar')[0][3] == tuple(round(v, 3) for v in PONTOS[1]), 10)
        and len(inicios('navegar')) == 1)
    dizer('pare')

    preparar(na_doca=True, sair=10.0)
    dizer('vá ao ponto 4')
    esperar(lambda: inicios('sair'), 10)
    t = dizer('pare')
    conferir('"pare" cancela a saída da doca', cancelada_depressa(t, 'sair'))
    time.sleep(2)
    conferir('e não navega depois', not inicios('navegar'))

    preparar(encaixar=10.0)
    dizer('dock')
    esperar(lambda: inicios('encaixar'), 10)
    t = dizer('pare')
    conferir('"pare" cancela o encaixe', cancelada_depressa(t, 'encaixar'))

    # ---------------------------------------------------------- condições
    preparar(bateria=0.1)
    dizer('vá ao ponto 4')
    time.sleep(3)
    conferir('bateria baixa: não sai', not inicios())
    preparar(bateria=0.1)
    dizer('volte para a doca')
    conferir('bateria baixa: voltar vale', esperar(lambda: inicios('navegar'), 10))

    preparar(tf=False)
    time.sleep(2)
    dizer('vá ao ponto 4')
    conferir('sem map->odom recente: desiste sem enviar', esperar(
        lambda: achou('NAO EXECUTADO', 'map→odom'), 30) and not inicios())

    navegando()
    robo.tf = False
    conferir('perda de map->odom no trajeto cancela', esperar(
        lambda: [e for e in fins('navegar') if e[3] == 'cancelada'], 20))

    preparar(navegar=40.0)
    alheio = Node('outro_programa', namespace='/robot1')
    executor.add_node(alheio)
    cliente = ActionClient(alheio, NavigateToPose, 'navigate_to_pose')
    cliente.wait_for_server(timeout_sec=5)
    cliente.send_goal_async(NavigateToPose.Goal())
    esperar(lambda: inicios('navegar'), 10)
    time.sleep(1)
    dizer('vá ao ponto 4')
    conferir('meta de outro programa ativa: não envia', esperar(
        lambda: achou('NAO EXECUTADO', 'outro programa'), 30) and len(inicios()) == 1)
    t = dizer('pare')
    conferir('"pare" cancela também a meta de outro programa', cancelada_depressa(t))

    preparar(recusar=True)
    dizer('vá ao ponto 4')
    conferir('meta recusada pelo servidor é informada', esperar(
        lambda: achou('meta recusada'), 10))

    navegando(ignorar_cancelamento=True)
    robo.duracao['navegar'] = 30.0
    dizer('pare')
    conferir('cancelamento não confirmado trava e avisa', esperar(
        lambda: achou('não foi confirmado'), 12))
    registro.clear()
    dizer('vá para a geladeira')
    conferir('travado: recusa novo movimento', esperar(
        lambda: achou('NAO EXECUTADO', 'não foi confirmado'), 10) and len(inicios()) == 1)
    robo.ignorar_cancelamento = False
    dizer('pare')
    conferir('"pare" repete o cancelamento e destrava',
             esperar(lambda: robo.ativas == 0, 5))
    registro.clear()
    time.sleep(1)
    robo.duracao['navegar'] = 1.0
    dizer('vá para a geladeira')
    conferir('depois de destravar volta a obedecer',
             esperar(lambda: achou('CONCLUIDO'), 10))

    # ---------------------------------------------------------- terminal de conversa
    preparar(navegar=30.0)
    falar = subprocess.Popen(
        ['ros2', 'run', 'llm_tb4', 'falar', '--ros-args', '-r', '__ns:=/robot1'],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        start_new_session=True)
    time.sleep(2)
    falar.stdin.write('vá ao ponto 4\n')
    falar.stdin.flush()
    conferir('falar: o pedido chega', esperar(lambda: inicios('navegar'), 10))
    t = time.monotonic()
    falar.stdin.write('\n')
    falar.stdin.flush()
    conferir('falar: Enter vazio para o robô', cancelada_depressa(t))
    falar.stdin.close()
    erros = falar.stderr.read()
    falar.wait(timeout=10)
    conferir('falar: sai sem erro', falar.returncode == 0 and 'terminate' not in erros
             and 'Traceback' not in erros)

    # ---------------------------------------------------------- encerramento
    encerrar(processo)
    sinais = (('Ctrl+C', signal.SIGINT), ('SIGTERM (docker stop)', signal.SIGTERM),
              ('SIGHUP (terminal fechado)', signal.SIGHUP), ('dois Ctrl+C', None))
    for nome, sinal in sinais:
        preparar(navegar=30.0)
        robo.pronto.clear()
        processo = subir('parking_brake:=false')
        esperar(lambda: robo.pronto[-1:] == [True], 40)
        time.sleep(1.5)
        dizer('vá ao ponto 4')
        comecou = esperar(lambda: inicios('navegar'), 10)
        t = time.monotonic()
        if sinal is None:
            os.killpg(processo.pid, signal.SIGINT)
            time.sleep(0.05)
            encerrar(processo, signal.SIGINT)
        else:
            encerrar(processo, sinal)
        conferir(f'{nome} com meta ativa: cancela antes de sair', comecou and esperar(
            lambda: [e for e in fins('navegar') if e[3] == 'cancelada'], 6)
            and fins('navegar')[0][0] - t < 4.0 and not achou('Traceback'))

    # ---------------------------------------------------------- freio
    preparar()
    robo.pronto.clear()
    processo = subir('bateria_simulada:=0.9')
    esperar(lambda: robo.pronto[-1:] == [True], 40)
    time.sleep(1)
    dizer('vá ao ponto 4')
    conferir('freio ligado: nada é enviado ao robô', esperar(
        lambda: achou('freio: não executado'), 10) and not inicios())
    encerrar(processo)

    print('FALHAS:', len(falhas), flush=True)
    executor.shutdown(timeout_sec=2)
    rclpy.try_shutdown()
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())

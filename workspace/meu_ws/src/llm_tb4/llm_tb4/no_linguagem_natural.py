"""Nó de linguagem natural do TurtleBot 4 com LLM local.

Segue o natural_language_nav do tutorial oficial (turtlebot4_openai_tutorials, ramo humble):
recebe texto em `user_input`, avisa em `ready_for_input` quando uma mensagem nova será
atendida e tem o parâmetro `parking_brake`, ligado por padrão. Com o freio ligado nada é
enviado ao robô; com ele desligado o robô SE MOVE.

As regras de quando mover, cancelar ou ignorar estão em missao.py; a conversa com o robô, em
execucao.py. Diferenças para o tutorial: specs/llm-integracao/PLANO.md.
Manual: https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html
"""
import collections
import signal
import sys
import threading
import time
from concurrent.futures import Future

import rclpy
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, String

from llm_tb4 import interpretador, mapa, missao, pontos

ESPERA_AO_ENCERRAR_S = 4.0   # para o cancelamento ser confirmado antes de o processo sair
SINAIS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)


def em_segundo_plano(funcao, *argumentos):
    """Roda em outra thread, para o "parar" chegar enquanto o modelo responde. A thread é
    daemon: o Ctrl+C não espera o fim de uma consulta (que pode durar o tempo limite)."""
    futuro = Future()

    def rodar():
        try:
            futuro.set_result(funcao(*argumentos))
        except Exception as erro:
            futuro.set_exception(erro)

    threading.Thread(target=rodar, daemon=True).start()
    return futuro


class NoLinguagemNatural(Node):
    def __init__(self):
        super().__init__('llm_node')
        fixo = ParameterDescriptor(read_only=True)
        self.modelo = self.declare_parameter('model_name', interpretador.MODELO, fixo).value
        self.freio = self.declare_parameter('parking_brake', True, fixo).value
        self.url = self.declare_parameter('ollama_url', interpretador.URL, fixo).value
        arquivo_mapa = self.declare_parameter('mapa', mapa.MAPA_PADRAO, fixo).value
        arquivo_pontos = self.declare_parameter(
            'arquivo_pontos', pontos.ARQUIVO_PADRAO, fixo).value
        self.bateria_simulada = self.declare_parameter('bateria_simulada', -1.0, fixo).value
        if not self.freio and self.bateria_simulada >= 0:
            raise SystemExit('bateria_simulada recusada com o freio desligado: o robô real '
                             'precisa da bateria real.')

        self.destinos = interpretador.carregar_destinos()
        try:
            rota = pontos.Rota(*pontos.ler_pontos(arquivo_pontos), self.destinos)
        except pontos.PontosInvalidos as erro:
            raise SystemExit(str(erro))
        no_mapa = mapa.verificador(arquivo_mapa)
        if not self.freio and rota.problemas(no_mapa):
            raise SystemExit(f'pontos da patrulha recusados pelo mapa: {rota.problemas(no_mapa)}')
        self.conferir_coordenada = rota.verificador(no_mapa)

        self.cfg = missao.Config(self.freio, rota.destino, rota.aproximacao())
        self.estado = missao.inicial(time.monotonic())
        self.fila = collections.deque()
        self.aplicando = False
        self.consultas = []          # (futuro, época, frase)
        self.pronto = None
        self.bateria = None
        self.robo = None
        self.navegador = None

        self.publicador = self.create_publisher(Bool, 'ready_for_input', 10)
        self.create_subscription(String, 'user_input', self.ao_receber, 10)
        if self.freio:
            self.create_subscription(BatteryState, 'battery_state',
                                     lambda m: setattr(self, 'bateria', m.percentage),
                                     qos_profile_sensor_data)
            self.get_logger().warn('FREIO DE ESTACIONAMENTO: nada será executado.')
        else:
            # Importados só aqui: com o freio ligado não há navegador nem cliente de ação.
            from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator

            from llm_tb4.execucao import Robo
            self.navegador = TurtleBot4Navigator()
            self.robo = Robo(self, self.navegador, self.aplicar)
            self.get_logger().warn('FREIO DESLIGADO: O ROBÔ VAI SE MOVER quando for pedido.')
        self.create_timer(0.05, self.concluir)
        self.avisar_pronto()
        # A primeira consulta carrega o modelo; só então o nó aceita pedidos (época 0).
        self.consultas.append(
            (em_segundo_plano(self.consultar, 'ponto 1', self.destinos), 0, None))

    # ------------------------------------------------------------ missão
    def sensores(self):
        return self.robo.sensores() if self.robo else missao.Sensores()

    def aplicar(self, evento):
        """Passa o evento pela missão e executa o que ela pedir, um de cada vez."""
        self.fila.append(evento)
        if self.aplicando:
            return
        self.aplicando = True
        try:
            while self.fila:
                self.estado, acoes = missao.decidir(
                    self.estado, self.fila.popleft(), self.sensores(), time.monotonic(),
                    self.cfg)
                for acao in acoes:
                    self.executar(*acao)
        finally:
            self.aplicando = False
        self.avisar_pronto()

    def executar(self, nome, *argumentos):
        if nome == 'log':
            nivel, texto = argumentos
            registrador = self.get_logger()
            # Uma chamada por nível: o rclpy não deixa a mesma linha de código mudar de nível.
            if nivel == 'info':
                registrador.info(texto)
            elif nivel == 'warn':
                registrador.warn(texto)
            else:
                registrador.error(texto)
        elif nome == 'interpretar':
            epoca, frase = argumentos
            self.get_logger().info(f'RECEBIDO: {frase!r}')
            futuro = em_segundo_plano(
                interpretador.interpretar, frase, self.destinos, self.carga(), self.consultar,
                self.conferir_coordenada)
            self.consultas.append((futuro, epoca, frase))
        elif self.robo is not None:      # 'enviar', 'cancelar', 'cancelar_tudo'
            getattr(self.robo, nome)(*argumentos)

    def avisar_pronto(self):
        pronto = missao.aceita_mensagem(self.estado)
        if pronto != self.pronto:
            self.pronto = pronto
            self.publicador.publish(Bool(data=pronto))

    # ------------------------------------------------------------ entrada
    def consultar(self, frase, destinos):
        return interpretador.perguntar_ao_ollama(frase, destinos, self.modelo, self.url)

    def carga(self):
        if self.robo is not None:
            leitura = self.robo.sensores()
            return leitura.bateria if missao.bateria_ok(leitura) else None
        return self.bateria_simulada if self.bateria_simulada >= 0 else self.bateria

    def ao_receber(self, mensagem):
        frase = mensagem.data
        parar = interpretador.pede_para_parar(interpretador.normalizar(frase))
        # Primeiro a missão (cancela o que for preciso), depois o registro.
        self.aplicar(missao.Mensagem(frase, parar))
        if parar:
            self.registrar(frase, interpretador.interpretar(frase, self.destinos, None))

    def concluir(self):
        for consulta in [c for c in self.consultas if c[0].done()]:
            self.consultas.remove(consulta)
            futuro, epoca, frase = consulta
            erro = futuro.exception()
            acao = None
            if frase is None:
                if erro:
                    self.get_logger().error(
                        f'o modelo {self.modelo} não respondeu em {self.url} '
                        f'({type(erro).__name__}); pedidos de parar continuam atendidos.')
            elif erro:
                self.get_logger().error(f'falha ao interpretar {frase!r}: {erro!r}')
            else:
                decisao = futuro.result()
                if self.estado.interpretando and self.estado.interpretando[0] == epoca:
                    self.registrar(frase, decisao)
                acao = decisao['acao']
            self.aplicar(missao.Ordem(epoca, frase or '', acao))
        self.aplicar(missao.Relogio())

    def registrar(self, frase, decisao):
        argumentos = decisao['acao']['argumentos'] if decisao['permitido'] else {}
        texto = (f'DECISAO: {frase!r} -> {interpretador.resumo(decisao)} {argumentos or ""} '
                 f'{decisao["motivo"]}').strip()
        if decisao['permitido']:
            sufixo = ' [freio: não executado]' if self.freio else ''
            self.get_logger().info(texto + sufixo)
        else:
            self.get_logger().warn(texto)

    def encerrar(self, executor):
        """Cancela a meta ativa e espera a confirmação, por até ESPERA_AO_ENCERRAR_S."""
        if self.estado.fase != missao.PARADO:
            self.get_logger().warn('ENCERRANDO: cancelando a meta ativa')
        self.aplicar(missao.Encerrar())
        limite = time.monotonic() + ESPERA_AO_ENCERRAR_S
        while self.estado.fase != missao.PARADO and time.monotonic() < limite:
            executor.spin_once(timeout_sec=0.05)
        # Mais um instante para os pedidos de cancelamento saírem.
        fim = time.monotonic() + 0.3
        while self.robo is not None and time.monotonic() < fim:
            executor.spin_once(timeout_sec=0.05)
        if self.estado.fase != missao.PARADO:
            self.get_logger().error('cancelamento NÃO confirmado: confira o robô')


def main(args=None):
    # Os sinais são nossos: o padrão do rclpy derrubaria o contexto antes do cancelamento.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    parar = threading.Event()
    for sinal in SINAIS:
        signal.signal(sinal, lambda *_: parar.set())
    no = executor = None
    try:
        no = NoLinguagemNatural()
        executor = SingleThreadedExecutor()
        executor.add_node(no)
        if no.navegador is not None:
            executor.add_node(no.navegador)
        while not parar.is_set() and rclpy.ok():
            executor.spin_once(timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    except SystemExit as erro:
        print(erro, file=sys.stderr)
        return 2
    finally:
        # Vale também para erro inesperado: a meta não pode ficar andando sem dono.
        if no is not None and executor is not None and rclpy.ok():
            no.encerrar(executor)
        rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())

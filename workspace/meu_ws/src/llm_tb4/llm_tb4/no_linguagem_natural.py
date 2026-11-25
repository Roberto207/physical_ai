"""Nó de linguagem natural do TurtleBot 4 com LLM local. NÃO TEM CÓDIGO DE MOVIMENTO.

Segue o natural_language_nav do tutorial oficial (turtlebot4_openai_tutorials, ramo humble):
recebe texto em `user_input`, avisa em `ready_for_input` quando aceita o próximo e tem o
parâmetro `parking_brake`. Diferenças registradas em specs/llm-integracao/PLANO.md: Ollama no
lugar da OpenAI, resposta validada em vez de exec(), e "parar" atendido mesmo com o nó ocupado.
Manual: https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html
"""
import signal
import sys
import threading
from concurrent.futures import Future

import rclpy
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, String

from llm_tb4 import interpretador, mapa


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
        freio = self.declare_parameter('parking_brake', True, fixo).value
        self.url = self.declare_parameter('ollama_url', interpretador.URL, fixo).value
        arquivo_mapa = self.declare_parameter('mapa', mapa.MAPA_PADRAO, fixo).value
        self.bateria_simulada = self.declare_parameter('bateria_simulada', -1.0, fixo).value
        if freio is not True:
            raise SystemExit('parking_brake:=false recusado: este nó não tem código de movimento.')

        self.destinos = interpretador.carregar_destinos()
        self.conferir_coordenada = mapa.verificador(arquivo_mapa)
        self.bateria = None
        self.pronto = False
        self.paradas = 0       # cada "parar" invalida a interpretação que estiver em andamento
        self.pendente = None   # (futuro, frase, paradas no momento do envio)

        self.publicador = self.create_publisher(Bool, 'ready_for_input', 10)
        self.create_subscription(String, 'user_input', self.ao_receber, 10)
        self.create_subscription(BatteryState, 'battery_state',
                                 lambda m: setattr(self, 'bateria', m.percentage),
                                 qos_profile_sensor_data)
        self.create_timer(0.05, self.concluir)
        self.get_logger().warn('FREIO DE ESTACIONAMENTO: nada será executado.')
        self.avisar_pronto(False)
        # A primeira consulta carrega o modelo; só então o nó se declara pronto.
        self.enviar(None)

    def avisar_pronto(self, pronto):
        self.pronto = pronto
        self.publicador.publish(Bool(data=pronto))

    def consultar(self, frase, destinos):
        return interpretador.perguntar_ao_ollama(frase, destinos, self.modelo, self.url)

    def carga(self):
        return self.bateria_simulada if self.bateria_simulada >= 0 else self.bateria

    def enviar(self, frase):
        if frase is None:
            futuro = em_segundo_plano(self.consultar, 'ponto 1', self.destinos)
        else:
            futuro = em_segundo_plano(
                interpretador.interpretar, frase, self.destinos, self.carga(), self.consultar,
                self.conferir_coordenada)
        self.pendente = (futuro, frase, self.paradas)

    def ao_receber(self, mensagem):
        frase = mensagem.data
        if interpretador.pede_para_parar(interpretador.normalizar(frase)):
            self.paradas += 1
            self.registrar(frase, interpretador.interpretar(frase, self.destinos, None))
            return
        if not self.pronto:
            self.get_logger().warn(f'OCUPADO: pedido ignorado: {frase!r}')
            return
        self.avisar_pronto(False)
        self.get_logger().info(f'RECEBIDO: {frase!r}')
        self.enviar(frase)

    def concluir(self):
        if self.pendente is None or not self.pendente[0].done():
            return
        futuro, frase, paradas = self.pendente
        self.pendente = None
        erro = futuro.exception()
        if frase is None:
            if erro:
                self.get_logger().error(
                    f'o modelo {self.modelo} não respondeu em {self.url} ({type(erro).__name__}); '
                    'pedidos de parar continuam atendidos.')
        elif paradas != self.paradas:
            self.get_logger().warn(f'DESCARTADO por um pedido de parar: {frase!r}')
        elif erro:
            self.get_logger().error(f'falha ao interpretar {frase!r}: {erro!r}')
        else:
            self.registrar(frase, futuro.result())
        self.avisar_pronto(True)

    def registrar(self, frase, decisao):
        argumentos = decisao['acao']['argumentos'] if decisao['permitido'] else {}
        texto = (f'DECISAO: {frase!r} -> {interpretador.resumo(decisao)} {argumentos or ""} '
                 f'{decisao["motivo"]}').strip()
        if decisao['permitido']:
            self.get_logger().info(texto + ' [freio: não executado]')
        else:
            self.get_logger().warn(texto)


def main(args=None):
    rclpy.init(args=args)
    no = None
    try:
        no = NoLinguagemNatural()
        rclpy.spin(no)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except SystemExit as erro:
        print(erro, file=sys.stderr)
        return 2
    finally:
        # O terminal e o ros2 launch podem mandar o Ctrl+C duas vezes; a segunda não pode
        # interromper o encerramento.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if no is not None:
            no.destroy_node()
        rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())

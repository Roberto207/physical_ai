"""Núcleo comum da patrulha e do LLM: pontos do mapa e conversa com o TurtleBot4Navigator.

Adaptado do patrol_loop.py oficial do TurtleBot 4, ramo Humble (Apache-2.0, Clearpath Robotics):
https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_python_tutorials/
        turtlebot4_python_tutorials/patrol_loop.py
"""
import math
import signal
import time

import rclpy
from nav2_simple_commander.robot_navigator import TaskResult
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import BatteryState
from tf2_msgs.msg import TFMessage

# Medidos com Publish Point no mapa_lab_novo, em metros no frame map
# (mapas/pontos_mapa_lab_novo.md). Única fonte: a patrulha e o LLM leem daqui.
DOCA = (-0.2025940716266632, 0.10048891603946686)
PONTOS = (
    (-0.5858250856399536, -0.8073815107345581),   # 1: perto da doca e da impressora
    (-3.549771785736084, -3.0633668899536133),    # 2: geladeira e micro-ondas
    (-5.608144283294678, -0.8229406476020813),    # 3: porta
    (-1.9671252965927124, 1.0304899215698242),    # 4: janela e mesa central
)
APROXIMACAO_DOCA = PONTOS[0]
BATERIA_BAIXA = 0.20
BATERIA_CRITICA = 0.10
TEMPO_DESTINO_S = 120


def iniciar_ros():
    """Os sinais ficam com o Python, e não com o rclpy: o tratador do rclpy derruba o contexto
    antes de o cancelTask() sair, e a meta continuaria ativa. Assim, Ctrl+C e "docker stop"
    (SIGTERM) viram KeyboardInterrupt com o ROS ainda de pé."""
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    signal.signal(signal.SIGTERM, signal.default_int_handler)


def criar_navegador():
    from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator
    return TurtleBot4Navigator()


def iniciar():
    """Inicia o ROS e devolve (navegador, bateria). bateria[0] é a carga de 0 a 1, ou None."""
    iniciar_ros()
    navegador = criar_navegador()
    bateria = [None]
    navegador.create_subscription(BatteryState, 'battery_state',
                                  lambda msg: bateria.__setitem__(0, msg.percentage),
                                  qos_profile_sensor_data)
    return navegador, bateria


def encerrar(navegador):
    try:
        navegador.cancelTask()
    except Exception:
        pass  # Pode não haver meta enviada.
    navegador.destroy_node()
    rclpy.try_shutdown()


def direcao(de, para):
    """Graus no frame map olhando de um ponto para outro (o Nav2 exige orientação)."""
    return math.degrees(math.atan2(para[1] - de[1], para[0] - de[0]))


def esperar_doca(navegador, valor, limite_s=20):
    prazo = time.monotonic() + limite_s
    while time.monotonic() < prazo:
        rclpy.spin_once(navegador, timeout_sec=0.2)
        if getattr(navegador, 'is_docked', None) is valor:
            return True
    return False


def esperar_localizacao(navegador):
    """Exige map→odom recente; a pose é marcada pelo operador no RViz (2D Pose Estimate)."""
    recebido = [False]

    def ao_receber_tf(mensagem):
        for transformacao in mensagem.transforms:
            if (transformacao.header.frame_id, transformacao.child_frame_id) != ('map', 'odom'):
                continue
            carimbo = transformacao.header.stamp
            idade = time.time() - carimbo.sec - carimbo.nanosec / 1e9
            if -2 < idade < 2:
                recebido[0] = True

    assinatura = navegador.create_subscription(
        TFMessage, 'tf', ao_receber_tf, qos_profile_sensor_data)
    try:
        for _ in range(30):
            rclpy.spin_once(navegador, timeout_sec=1)
            if recebido[0]:
                navegador.info('Transformação map→odom recente; localização disponível')
                return True
        navegador.error('Sem map→odom recente: use 2D Pose Estimate no RViz e confira o laser')
        return False
    finally:
        navegador.destroy_subscription(assinatura)


def esperar_servidores(navegador, limite_s=30):
    """Ações de navegação, dock e undock com prazo. O waitUntilNav2Active oficial espera
    serviços de ciclo de vida sem prazo e pode travar no Discovery Server."""
    navegador.info('Conferindo ações de navegação, dock e undock...')
    prazo = time.monotonic() + limite_s
    while time.monotonic() < prazo:
        if (navegador.nav_to_pose_client.server_is_ready()
                and navegador.dock_action_client.server_is_ready()
                and navegador.undock_action_client.server_is_ready()):
            navegador.info('Servidores de ação disponíveis')
            return True
        rclpy.spin_once(navegador, timeout_sec=0.5)
    navegador.error(f'Servidores de ação indisponíveis após {limite_s} s; nenhum movimento')
    return False


def esperar_bateria(navegador, bateria, limite_s=15):
    prazo = time.monotonic() + limite_s
    while bateria[0] is None and time.monotonic() < prazo:
        rclpy.spin_once(navegador, timeout_sec=0.2)
    return bateria[0]


def sair_da_doca(navegador):
    navegador.undock()
    if not esperar_doca(navegador, False):
        navegador.error('Undock não confirmado')
        return False
    return True


def navegar(navegador, coordenadas, proximo, nome, deve_parar=None):
    """Vai a coordenadas olhando para `proximo`. deve_parar(): se der True, cancela a meta."""
    x, y = coordenadas
    destino = navegador.getPoseStamped([x, y], direcao(coordenadas, proximo))
    navegador.info(f'Indo a {nome}: x={x:.3f}, y={y:.3f}')
    if navegador.goToPose(destino) is False:
        navegador.error(f'{nome}: meta recusada')
        return False
    prazo = time.monotonic() + TEMPO_DESTINO_S
    while not navegador.isTaskComplete():
        if deve_parar is not None and deve_parar():
            navegador.cancelTask()
            navegador.warn(f'{nome}: meta cancelada')
            return False
        if time.monotonic() >= prazo:
            navegador.error(f'{nome}: excedeu {TEMPO_DESTINO_S} s; cancelando a meta')
            navegador.cancelTask()
            return False
        time.sleep(0.1)
    resultado = navegador.getResult()
    if resultado != TaskResult.SUCCEEDED:
        navegador.error(f'{nome}: navegação falhou ({resultado})')
        return False
    navegador.info(f'{nome}: destino alcançado')
    return True


def voltar_doca(navegador, deve_parar=None):
    """Ponto 1 virado para a doca, depois dock."""
    if not navegar(navegador, APROXIMACAO_DOCA, DOCA, 'aproximação da doca', deve_parar):
        return False
    navegador.dock()
    if not esperar_doca(navegador, True):
        navegador.error('Dock não confirmado; conferir o robô fisicamente')
        return False
    navegador.info('Dock confirmado')
    return True

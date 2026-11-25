#!/usr/bin/env python3
"""Loop pelo ponto 1 até 3 e 4, refazendo o caminho de volta até o 1."""

import math
import sys
import time

import rclpy
from nav2_simple_commander.robot_navigator import TaskResult
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState
from tf2_msgs.msg import TFMessage
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator


# Mesmas coordenadas do patrol_loop.py existente. Índices humanos:
# ponto 1 = aproximação da doca; ponto 3 e ponto 4 = destinos de patrulha.
DOCA = (-0.2025940716266632, 0.10048891603946686)
PONTOS = (
    (-0.5858250856399536, -0.8073815107345581),  # ponto 1
    (-3.549771785736084, -3.0633668899536133),   # ponto 2 (não usado)
    (-5.608144283294678, -0.8229406476020813),   # ponto 3
    (-1.9671252965927124, 1.0304899215698242),   # ponto 4
)
PONTO_1, PONTO_3, PONTO_4 = PONTOS[0], PONTOS[2], PONTOS[3]
BATERIA_BAIXA = 0.20
BATERIA_CRITICA = 0.10
TEMPO_DESTINO_S = 120


def pose(navegador, coordenadas, proximo):
    x, y = coordenadas
    yaw = math.degrees(math.atan2(proximo[1] - y, proximo[0] - x))
    return navegador.getPoseStamped([x, y], yaw)


def esperar_doca(navegador, valor, limite_s=20):
    prazo = time.monotonic() + limite_s
    while time.monotonic() < prazo:
        rclpy.spin_once(navegador, timeout_sec=0.2)
        if getattr(navegador, 'is_docked', None) is valor:
            return True
    return False


def esperar_localizacao(navegador):
    recebeu = [False]

    def ao_receber_tf(mensagem):
        for transformacao in mensagem.transforms:
            if (transformacao.header.frame_id, transformacao.child_frame_id) != ('map', 'odom'):
                continue
            carimbo = transformacao.header.stamp
            idade = time.time() - carimbo.sec - carimbo.nanosec / 1e9
            if -2 < idade < 2:
                recebeu[0] = True

    assinatura = navegador.create_subscription(
        TFMessage, 'tf', ao_receber_tf, qos_profile_sensor_data)
    try:
        for _ in range(30):
            rclpy.spin_once(navegador, timeout_sec=1)
            if recebeu[0]:
                navegador.info('Transformação map→odom recente; localização disponível')
                return True
        navegador.error('Sem map→odom recente: marque 2D Pose Estimate no RViz e confira o laser')
        return False
    finally:
        navegador.destroy_subscription(assinatura)


def esperar_servidores(navegador, limite_s=30):
    navegador.info('Conferindo ações de navegação, dock e undock...')
    prazo = time.monotonic() + limite_s
    while time.monotonic() < prazo:
        if (navegador.nav_to_pose_client.server_is_ready()
                and navegador.dock_action_client.server_is_ready()
                and navegador.undock_action_client.server_is_ready()):
            navegador.info('Servidores de ação disponíveis')
            return True
        rclpy.spin_once(navegador, timeout_sec=0.5)
    navegador.error('Servidores de ação indisponíveis após 30 s; nenhum movimento enviado')
    return False


def navegar(navegador, coordenadas, proximo, nome):
    destino = pose(navegador, coordenadas, proximo)
    navegador.info(f'Indo a {nome}: x={coordenadas[0]:.3f}, y={coordenadas[1]:.3f}')
    if navegador.goToPose(destino) is False:
        navegador.error(f'{nome}: meta recusada')
        return False
    prazo = time.monotonic() + TEMPO_DESTINO_S
    while not navegador.isTaskComplete():
        if time.monotonic() >= prazo:
            navegador.error(f'{nome}: excedeu {TEMPO_DESTINO_S} s; cancelando a meta')
            navegador.cancelTask()
            return False
        time.sleep(0.1)
    resultado = navegador.getResult()
    if resultado != TaskResult.SUCCEEDED:
        navegador.error(f'{nome}: navegação falhou ({resultado}); interrompendo o loop')
        return False
    navegador.info(f'{nome}: destino alcançado')
    return True


def voltar_doca(navegador):
    if not navegar(navegador, PONTO_1, DOCA, 'ponto 1, aproximação da doca'):
        return False
    navegador.dock()
    if not esperar_doca(navegador, True):
        navegador.error('Dock não confirmado; confira o robô fisicamente')
        return False
    navegador.info('Dock confirmado')
    return True


def main():
    rclpy.init()
    navegador = TurtleBot4Navigator()
    bateria = [None]
    navegador.create_subscription(
        BatteryState, 'battery_state',
        lambda msg: bateria.__setitem__(0, msg.percentage), qos_profile_sensor_data)
    try:
        if not esperar_doca(navegador, True):
            navegador.error('Robô não confirmado na doca: loop não iniciado')
            return 2
        if not esperar_localizacao(navegador):
            return 7
        if not esperar_servidores(navegador):
            return 8

        prazo = time.monotonic() + 15
        while bateria[0] is None and time.monotonic() < prazo:
            rclpy.spin_once(navegador, timeout_sec=0.2)
        if bateria[0] is None or bateria[0] < BATERIA_BAIXA:
            navegador.error('Bateria ausente ou abaixo de 20%: loop não iniciado')
            return 3

        navegador.undock()
        if not esperar_doca(navegador, False):
            navegador.error('Undock não confirmado: loop interrompido')
            return 4

        # Vai ao ponto 1 e repete: 1 → 3 → 4 → 3 → 1.
        if not navegar(navegador, PONTO_1, PONTO_3, 'ponto 1'):
            return 6
        volta = 0
        while True:
            if bateria[0] is None or bateria[0] < BATERIA_BAIXA:
                navegador.info('Bateria baixa ou leitura ausente; tentando voltar à doca')
                return 0 if voltar_doca(navegador) else 5

            rota = ((PONTO_3, PONTO_4, 'ponto 3'),
                    (PONTO_4, PONTO_3, 'ponto 4'),
                    (PONTO_3, PONTO_1, 'ponto 3 no retorno'),
                    (PONTO_1, PONTO_3, 'ponto 1'))

            for atual, proximo, nome in rota:
                if bateria[0] is None or bateria[0] < BATERIA_CRITICA:
                    navegador.error('Bateria crítica ou leitura ausente; tentando voltar à doca')
                    return 0 if voltar_doca(navegador) else 5
                if bateria[0] < BATERIA_BAIXA:
                    navegador.info('Bateria baixa; tentando voltar à doca')
                    return 0 if voltar_doca(navegador) else 5
                if not navegar(navegador, atual, proximo, nome):
                    return 6

            volta += 1
            navegador.info(f'Loop {volta} concluído; repetindo 1 → 3 → 4 → 3 → 1')
    except KeyboardInterrupt:
        try:
            navegador.cancelTask()
        except Exception:
            pass
        navegador.info('Interrompido. Confirme a posição física do robô; Ctrl+C não garante retorno à doca.')
        return 130
    finally:
        navegador.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())

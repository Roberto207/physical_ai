#!/usr/bin/env python3
"""Adaptação do patrol_loop.py oficial do TurtleBot 4, ramo Humble, para mapa_lab_novo.

Fonte: https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/
        turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py
Copyright 2023 Clearpath Robotics, Inc.; licença Apache-2.0.
"""

import argparse
import math
import sys
import time

import rclpy
from nav2_simple_commander.robot_navigator import TaskResult
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState
from tf2_msgs.msg import TFMessage
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator


# Coordenadas medidas com Publish Point no mapa_lab_novo, em metros no frame map.
# A orientação inicial é marcada manualmente no RViz com 2D Pose Estimate.
DOCA = (-0.2025940716266632, 0.10048891603946686)
PONTOS = (
    (-0.5858250856399536, -0.8073815107345581),
    (-3.549771785736084, -3.0633668899536133),
    (-5.608144283294678, -0.8229406476020813),
    (-1.9671252965927124, 1.0304899215698242),
)
APROXIMACAO_DOCA = PONTOS[0]
BATERIA_BAIXA = 0.20
BATERIA_CRITICA = 0.10
TEMPO_DESTINO_S = 120


def pose(navegador, coordenadas, proximo):
    x, y = coordenadas
    # Nav2 exige orientação, calculada pela direção do ponto seguinte.
    direcao = math.degrees(math.atan2(proximo[1] - y, proximo[0] - x))
    return navegador.getPoseStamped([x, y], direcao)


def esperar_doca(navegador, valor, limite_s=20):
    prazo = time.monotonic() + limite_s
    while time.monotonic() < prazo:
        rclpy.spin_once(navegador, timeout_sec=0.2)
        if getattr(navegador, 'is_docked', None) is valor:
            return True
    return False


def esperar_localizacao(navegador):
    """Exigir map→odom recente; a pose é marcada pelo operador no RViz."""
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
    """Exigir ações disponíveis com prazo, sem a espera indefinida do exemplo."""
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
        navegador.error(f'{nome}: navegação falhou ({resultado}); interrompendo a patrulha')
        return False
    navegador.info(f'{nome}: destino alcançado')
    return True


def voltar_doca(navegador):
    if not navegar(navegador, APROXIMACAO_DOCA, DOCA, 'aproximação da doca'):
        return False
    navegador.dock()
    if not esperar_doca(navegador, True):
        navegador.error('Dock não confirmado; conferir o robô fisicamente')
        return False
    navegador.info('Dock confirmado')
    return True


def main():
    argumentos = argparse.ArgumentParser(description='Patrulha TB4 Humble no mapa_lab_novo')
    argumentos.add_argument('--voltas', type=int, default=1,
                            help='1 para primeira prova; 0 para repetir até Ctrl+C')
    argumentos.add_argument('--verificar-localizacao', action='store_true',
                            help='confere map→odom e Nav2 sem mover o robô')
    opcoes, args_ros = argumentos.parse_known_args()
    if opcoes.voltas < 0:
        argumentos.error('--voltas deve ser 0 ou maior')
    rclpy.init(args=args_ros)
    navegador = TurtleBot4Navigator()
    bateria = [None]
    navegador.create_subscription(BatteryState, 'battery_state',
                                  lambda msg: bateria.__setitem__(0, msg.percentage),
                                  qos_profile_sensor_data)
    try:
        if not esperar_doca(navegador, True):
            navegador.error('Robô não confirmado na doca: patrulha não iniciada')
            return 2

        if not esperar_localizacao(navegador):
            return 7
        # A pose veio do RViz antes deste nó existir. O waitUntilNav2Active
        # oficial espera serviços de ciclo de vida sem prazo e pode travar no
        # Discovery Server. Conferimos a TF e as ações necessárias com prazo.
        if not esperar_servidores(navegador):
            return 8
        if opcoes.verificar_localizacao:
            navegador.info('Localização e Nav2 verificados; nenhum movimento enviado')
            return 0

        prazo = time.monotonic() + 15
        while bateria[0] is None and time.monotonic() < prazo:
            rclpy.spin_once(navegador, timeout_sec=0.2)
        if bateria[0] is None or bateria[0] < BATERIA_BAIXA:
            navegador.error('Bateria ausente ou abaixo de 20%: patrulha não iniciada')
            return 3

        navegador.undock()
        if not esperar_doca(navegador, False):
            navegador.error('Undock não confirmado: patrulha interrompida')
            return 4

        volta = 0
        while opcoes.voltas == 0 or volta < opcoes.voltas:
            for indice, coordenadas in enumerate(PONTOS, start=1):
                if bateria[0] is None or bateria[0] < BATERIA_CRITICA:
                    navegador.error('Bateria crítica ou leitura ausente; retornando à doca')
                    return 0 if voltar_doca(navegador) else 5
                if bateria[0] < BATERIA_BAIXA:
                    navegador.info('Bateria baixa; retornando à doca')
                    return 0 if voltar_doca(navegador) else 5
                if indice < len(PONTOS):
                    proximo = PONTOS[indice]
                elif opcoes.voltas == 0:
                    proximo = PONTOS[0]
                else:
                    proximo = DOCA
                if not navegar(navegador, coordenadas, proximo, f'ponto {indice}'):
                    return 6
            volta += 1
            navegador.info(f'Volta {volta} concluída')

        return 0 if voltar_doca(navegador) else 5
    except KeyboardInterrupt:
        try:
            navegador.cancelTask()
        except Exception:
            pass  # Pode ter sido interrompido antes de enviar uma meta.
        navegador.info('Interrompido. Confirme a posição e a doca fisicamente.')
        return 130
    finally:
        navegador.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())

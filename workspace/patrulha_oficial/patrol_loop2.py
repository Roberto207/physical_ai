#!/usr/bin/env python3
"""Percorre os pontos 1, 2, 3, 4, 3, 2, 1 e retorna à doca."""

import argparse
import sys
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from rclpy.utilities import remove_ros_args
from sensor_msgs.msg import BatteryState
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator

from patrol_loop import (
    BATERIA_BAIXA,
    DOCA,
    PONTOS,
    esperar_doca,
    esperar_localizacao,
    esperar_servidores,
    navegar,
    voltar_doca,
)


def main():
    argumentos = argparse.ArgumentParser(
        description='Patrulha de ida e volta pelos pontos 1, 2, 3 e 4',
        allow_abbrev=False)
    argumentos.add_argument(
        '--verificar-localizacao', action='store_true',
        help='confere map→odom e Nav2 sem mover o robô')
    argumentos.add_argument(
        '--voltar-doca', action='store_true',
        help='navega até a aproximação e encaixa na doca, sem iniciar a patrulha')
    # Opção digitada errado é erro: ignorá-la faria o robô andar sem o operador querer.
    opcoes = argumentos.parse_args(remove_ros_args(sys.argv)[1:])

    rclpy.init()
    navegador = TurtleBot4Navigator()
    bateria = [None]
    navegador.create_subscription(
        BatteryState, 'battery_state',
        lambda msg: bateria.__setitem__(0, msg.percentage), qos_profile_sensor_data)

    try:
        if opcoes.voltar_doca:
            if esperar_doca(navegador, True):
                navegador.info('Robô já está encaixado na doca')
                return 0
            if not esperar_doca(navegador, False):
                navegador.error('Não foi possível confirmar se o robô está encaixado')
                return 2
        elif not esperar_doca(navegador, True):
            navegador.error('Robô não confirmado na doca: patrulha não iniciada')
            return 2
        if not esperar_localizacao(navegador):
            return 7
        if not esperar_servidores(navegador):
            return 8
        if opcoes.verificar_localizacao:
            navegador.info('Localização e Nav2 verificados; nenhum movimento enviado')
            return 0
        if opcoes.voltar_doca:
            navegador.info('Modo retorno à doca solicitado')
            return 0 if voltar_doca(navegador) else 5

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

        # Ida até o ponto 4 e retorno pelo mesmo caminho: 1, 2, 3, 4, 3, 2, 1.
        rota = list(enumerate(PONTOS, start=1))
        rota.extend((indice, PONTOS[indice - 1]) for indice in (3, 2, 1))
        for posicao, (numero_ponto, coordenadas) in enumerate(rota):
            if bateria[0] is None or bateria[0] < BATERIA_BAIXA:
                navegador.info('Bateria baixa ou leitura ausente; tentando voltar à doca')
                return 0 if voltar_doca(navegador) else 5

            proximo = rota[posicao + 1][1] if posicao + 1 < len(rota) else DOCA
            sufixo = ' no retorno' if posicao >= len(PONTOS) else ''
            if not navegar(
                    navegador, coordenadas, proximo,
                    f'ponto {numero_ponto}{sufixo}'):
                return 6

        navegador.info('Rota de ida e volta concluída; encaixando na doca')
        return 0 if voltar_doca(navegador) else 5
    except KeyboardInterrupt:
        try:
            navegador.cancelTask()
        except Exception:
            pass
        navegador.info('Interrompido. Confirme a posição física; '
                       'Ctrl+C não garante retorno à doca.')
        return 130
    finally:
        navegador.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Patrulha do TurtleBot 4 no mapa_lab_novo. MOVE O ROBÔ.

    python3 patrulha.py voltas N       1→2→3→4 por N voltas (0 = até Ctrl+C) e doca
    python3 patrulha.py ida-e-volta    1,2,3,4,3,2,1 e doca
    python3 patrulha.py continuo       1, depois 3→4→3→1 até Ctrl+C ou bateria baixa
    python3 patrulha.py doca           só volta e encaixa na doca
    (todos aceitam --verificar-localizacao, que confere tudo sem mover)

Começa na doca (menos `doca`), com a pose marcada no RViz. Bateria baixa: volta à doca.
Pelo PC do lab use scripts/patrulha.sh, que passa o namespace do robô.
"""
import argparse
import sys

from rclpy.utilities import remove_ros_args

import robo
from robo import BATERIA_BAIXA, BATERIA_CRITICA, DOCA, PONTOS

P1, P2, P3, P4 = PONTOS


def pernas_voltas(voltas):
    """Uma volta 1→2→3→4. O último ponto olha para a doca, ou para o 1 se não tem fim."""
    fim = P1 if voltas == 0 else DOCA
    proximos = (*PONTOS[1:], fim)
    return [(p, prox, f'ponto {i}') for i, (p, prox) in enumerate(zip(PONTOS, proximos), 1)]


def pernas_ida_e_volta():
    numeros = (1, 2, 3, 4, 3, 2, 1)
    pernas = []
    for posicao, n in enumerate(numeros):
        proximo = PONTOS[numeros[posicao + 1] - 1] if posicao + 1 < len(numeros) else DOCA
        sufixo = ' no retorno' if posicao >= len(PONTOS) else ''
        pernas.append((PONTOS[n - 1], proximo, f'ponto {n}{sufixo}'))
    return pernas


PERNAS_CONTINUO = [(P3, P4, 'ponto 3'), (P4, P3, 'ponto 4'),
                   (P3, P1, 'ponto 3 no retorno'), (P1, P3, 'ponto 1')]


def bateria_baixa(navegador, carga):
    if carga is None or carga < BATERIA_CRITICA:
        navegador.error('Bateria crítica ou leitura ausente; retornando à doca')
        return True
    if carga < BATERIA_BAIXA:
        navegador.info('Bateria baixa; retornando à doca')
        return True
    return False


def patrulhar(navegador, bateria, pernas, voltas, inicio=()):
    """Percorre `inicio` uma vez e `pernas` por `voltas` (0 = sem fim); termina na doca."""
    for coordenadas, proximo, nome in inicio:
        if not robo.navegar(navegador, coordenadas, proximo, nome):
            return 6
    volta = 0
    while voltas == 0 or volta < voltas:
        for coordenadas, proximo, nome in pernas:
            if bateria_baixa(navegador, bateria[0]):
                return 0 if robo.voltar_doca(navegador) else 5
            if not robo.navegar(navegador, coordenadas, proximo, nome):
                return 6
        volta += 1
        navegador.info(f'Volta {volta} concluída')
    return 0 if robo.voltar_doca(navegador) else 5


def ler_opcoes(argv):
    leitor = argparse.ArgumentParser(description='Patrulha TB4 no mapa_lab_novo',
                                     allow_abbrev=False)
    leitor.add_argument('--verificar-localizacao', action='store_true',
                        help='confere doca, map→odom e Nav2 sem mover o robô')
    modos = leitor.add_subparsers(dest='modo', required=True)
    voltas = modos.add_parser('voltas', help='1→2→3→4 por N voltas e doca')
    voltas.add_argument('n', type=int, help='número de voltas; 0 = até Ctrl+C')
    modos.add_parser('ida-e-volta', help='1,2,3,4,3,2,1 e doca')
    modos.add_parser('continuo', help='1, depois 3→4→3→1 até Ctrl+C ou bateria baixa')
    modos.add_parser('doca', help='só volta e encaixa na doca')
    # Opção digitada errado é erro: ignorá-la faria o robô andar sem o operador querer.
    opcoes = leitor.parse_args(argv)
    if opcoes.modo == 'voltas' and opcoes.n < 0:
        leitor.error('voltas deve ser 0 ou maior')
    return opcoes


def rodar(navegador, bateria, opcoes):
    if opcoes.modo == 'doca':
        if robo.esperar_doca(navegador, True, limite_s=5):
            navegador.info('Robô já está encaixado na doca')
            return 0
        if not robo.esperar_doca(navegador, False):
            navegador.error('Não foi possível confirmar se o robô está encaixado')
            return 2
    elif not robo.esperar_doca(navegador, True):
        navegador.error('Robô não confirmado na doca: patrulha não iniciada')
        return 2
    if not robo.esperar_localizacao(navegador):
        return 7
    if not robo.esperar_servidores(navegador):
        return 8
    if opcoes.verificar_localizacao:
        navegador.info('Localização e Nav2 verificados; nenhum movimento enviado')
        return 0
    if opcoes.modo == 'doca':
        return 0 if robo.voltar_doca(navegador) else 5

    carga = robo.esperar_bateria(navegador, bateria)
    if carga is None or carga < BATERIA_BAIXA:
        navegador.error('Bateria ausente ou abaixo de 20%: patrulha não iniciada')
        return 3
    if not robo.sair_da_doca(navegador):
        return 4

    if opcoes.modo == 'voltas':
        return patrulhar(navegador, bateria, pernas_voltas(opcoes.n), opcoes.n)
    if opcoes.modo == 'ida-e-volta':
        return patrulhar(navegador, bateria, pernas_ida_e_volta(), 1)
    return patrulhar(navegador, bateria, PERNAS_CONTINUO, 0, inicio=[(P1, P3, 'ponto 1')])


def main():
    opcoes = ler_opcoes(remove_ros_args(sys.argv)[1:])
    navegador, bateria = robo.iniciar()
    try:
        return rodar(navegador, bateria, opcoes)
    except KeyboardInterrupt:
        navegador.cancelTask()
        navegador.info('Interrompido; meta cancelada. Confirme a posição e a doca fisicamente.')
        return 130
    finally:
        robo.encerrar(navegador)


if __name__ == '__main__':
    sys.exit(main())

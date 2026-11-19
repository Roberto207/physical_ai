#!/usr/bin/env python3
"""Vigia de um cenário L1: decide quando parar o teste e guarda o que o veredito precisa.

Substitui o laço do antigo infra/docker/l1_dentro.sh (tag jazzy-final). Sobe junto com a
patrulha pelo l1.launch.py. Quando este nó termina, o l1.launch.py encerra o launch inteiro.

O que ele faz, de 2 em 2 s:
- Nav2 que não subiu (SIM-06): se o /rosout mostrar "Aborting bringup" nos primeiros
  `janela_nav2_s` segundos, grava o marcador `nav2_abortou` na pasta de evidências e sai. O
  teste_l1.sh, no host, vê o marcador e roda o cenário de novo num container novo.
- Ponto esperado: confere o JSONL da patrulha com o conferir_l1 (modo --pronto).
- Tempo-limite: `limite_s` segundos de relógio, contados a partir de `espera_s` (a hora em que
  o l1.launch.py sobe a patrulha). Este nó sobe antes, junto com o Nav2, para não perder o log.
Ao parar, grava o ambiente.txt (motivo, RViz, nós) e, se a patrulha ainda roda e
`sinal_no_fim` for true, grava o sinal.txt com o instante e manda SIGINT direto para o nó da
patrulha (PAT-15: ela precisa cancelar, gravar o resumo e sair em até 3 s).

Por que o SIGINT vai para o processo do nó, e não para o launch: é o mesmo motivo do script
antigo. O sinal precisa chegar ao nó, e o launch o repassaria para todos os processos de uma vez.
"""
import glob
import os
import subprocess
import time

import rclpy
from rcl_interfaces.msg import Log
from rclpy.node import Node

try:
    from rclpy.executors import ExternalShutdownException
except ImportError:  # rclpy antigo: o Ctrl+C chega só como KeyboardInterrupt
    ExternalShutdownException = KeyboardInterrupt

from lab_tb4 import conferir_l1

PROCESSO_PATRULHA = 'lib/patrulha_tb4/patrulha'


def _rodando(padrao):
    return subprocess.run(['pgrep', '-f', padrao], stdout=subprocess.DEVNULL).returncode == 0


class VigiaL1(Node):

    def __init__(self):
        super().__init__('vigia_l1')
        self.cenario = self.declare_parameter('cenario', '').value
        self.pasta = self.declare_parameter('pasta', '/evidencias').value
        self.limite_s = float(self.declare_parameter('limite_s', 900.0).value)
        self.sinal_no_fim = bool(self.declare_parameter('sinal_no_fim', True).value)
        self.olhar_nav2 = bool(self.declare_parameter('olhar_nav2', True).value)
        self.janela_nav2_s = float(self.declare_parameter('janela_nav2_s', 15.0).value)
        self.espera_s = float(self.declare_parameter('espera_s', 0.0).value)
        self.inicio = time.monotonic()
        self.terminou = False
        self.motivo = 'a patrulha encerrou sozinha'
        self.create_subscription(Log, '/rosout', self._ao_log, 50)
        self.create_timer(2.0, self._conferir)

    def _ao_log(self, msg):
        if (self.olhar_nav2 and not self.terminou and 'Aborting bringup' in msg.msg
                and time.monotonic() - self.inicio <= self.janela_nav2_s):
            with open(os.path.join(self.pasta, 'nav2_abortou'), 'w', encoding='utf-8') as arq:
                arq.write(f'{msg.name}: {msg.msg}\n')
            self.parar('o Nav2 leve não subiu (Aborting bringup)', mandar_sinal=False)

    def _conferir(self):
        decorrido = time.monotonic() - self.inicio - self.espera_s   # desde a patrulha subir
        if self.terminou or decorrido < 0:
            return
        if decorrido > self.limite_s:
            self.parar(f'tempo esgotado ({self.limite_s:.0f} s)')
            return
        jsonl = sorted(glob.glob(os.path.join(self.pasta, '*.jsonl')))
        if jsonl and conferir_l1.main([self.cenario, jsonl[0], '--pronto']) == 0:
            self.parar('o cenário chegou ao ponto esperado')

    def gravar_ambiente(self, nos=True):
        lista = 'não coletado'
        if nos:
            try:
                saida = subprocess.run(['ros2', 'node', 'list', '--no-daemon', '--spin-time', '3'],
                                       capture_output=True, text=True, timeout=10)
                lista = ' '.join(saida.stdout.split())
            except (OSError, subprocess.SubprocessError) as erro:
                lista = f'falhou ({erro})'
        rviz = 'RODANDO' if _rodando('rviz2') else 'nenhum processo (AMB-03)'
        with open(os.path.join(self.pasta, 'ambiente.txt'), 'w', encoding='utf-8') as arq:
            arq.write(f'parada: {self.motivo}\nrviz2: {rviz}\nnos: {lista}\n')

    def parar(self, motivo, mandar_sinal=True):
        self.terminou = True
        self.motivo = motivo
        self.get_logger().info(f'parando o cenário {self.cenario}: {motivo}')
        self.gravar_ambiente()
        if mandar_sinal and self.sinal_no_fim and _rodando(PROCESSO_PATRULHA):
            with open(os.path.join(self.pasta, 'sinal.txt'), 'w', encoding='utf-8') as arq:
                arq.write(f'{time.time():.6f}\n')
            subprocess.run(['pkill', '-INT', '-f', PROCESSO_PATRULHA])
            for _ in range(20):            # até 10 s para a patrulha sair sozinha
                if not _rodando(PROCESSO_PATRULHA):
                    break
                time.sleep(0.5)
            subprocess.run(['pkill', '-KILL', '-f', PROCESSO_PATRULHA])
        raise SystemExit(0)


def main():
    rclpy.init()
    vigia = VigiaL1()
    try:
        rclpy.spin(vigia)
    except SystemExit:
        pass
    except (KeyboardInterrupt, ExternalShutdownException):
        # O launch está encerrando porque a patrulha saiu sozinha: registra isso, sem pedir a
        # lista de nós (eles já estão sendo derrubados).
        if not vigia.terminou:
            vigia.gravar_ambiente(nos=False)
    finally:
        vigia.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

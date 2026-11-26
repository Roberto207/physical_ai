#!/usr/bin/env python3
"""Nó de linguagem natural do TurtleBot 4 com LLM local (Ollama).

Como o natural_language_nav do tutorial oficial (turtlebot4_openai_tutorials, ramo humble):
recebe texto em `user_input`, avisa em `ready_for_input` e tem freio, ligado por padrão.
Com o freio ligado, interpreta e registra, mas não cria o navegador: nada se move.
Com `-p freio:=false`, O ROBÔ SE MOVE a cada pedido aceito.

Uma ordem por vez. Qualquer mensagem nova durante um movimento cancela a meta; depois a
mensagem é interpretada ("pare" só registra a parada). Ctrl+C e "docker stop" cancelam a meta.
Pelo PC do lab use scripts/llm.sh (freio) ou scripts/llm.sh mover.
"""
import queue
import sys
import threading
from pathlib import Path

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, String

from interpretar import LOCAIS, MODELO, interpretar, perguntar_ao_ollama, resumo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import robo  # noqa: E402  (robo.py fica na raiz do repositório)


def estado_doca(navegador):
    """True encaixado, False fora, None desconhecido (dock_status ainda não chegou)."""
    for _ in range(5):
        rclpy.spin_once(navegador, timeout_sec=0.1)
    return getattr(navegador, 'is_docked', None)


def executar(navegador, decisao, deve_parar, log):
    acao, doca = decisao['acao'], estado_doca(navegador)
    if doca is None:
        log.error('estado da doca desconhecido (dock_status não chegou): nada enviado')
        return
    if acao == 'encaixar':
        if doca:
            log.info('já encaixado')
        else:
            navegador.dock()
            if not robo.esperar_doca(navegador, True):
                log.error('dock não confirmado')
    elif acao == 'sair_da_base':
        if doca:
            robo.sair_da_doca(navegador)
        else:
            log.info('já está fora da doca')
    elif acao == 'voltar_para_base':
        if doca:
            log.info('já encaixado')
        else:
            robo.voltar_doca(navegador, deve_parar)
    elif acao == 'ir_para':
        if doca and not robo.sair_da_doca(navegador):
            return
        numero = LOCAIS[decisao['local']][0]
        # Como na patrulha: chega olhando para o ponto seguinte.
        alvo, proximo = robo.PONTOS[numero - 1], robo.PONTOS[numero % len(robo.PONTOS)]
        robo.navegar(navegador, alvo, proximo, f'ponto {numero}', deve_parar)


def main():
    robo.iniciar_ros()
    no = Node('llm_node')
    freio = no.declare_parameter('freio', True).value
    log = no.get_logger()
    fila = queue.Queue()
    bateria = [None]
    no.create_subscription(String, 'user_input', lambda m: fila.put(m.data), 10)
    no.create_subscription(BatteryState, 'battery_state',
                           lambda m: bateria.__setitem__(0, m.percentage),
                           qos_profile_sensor_data)
    pronto = no.create_publisher(Bool, 'ready_for_input', 10)
    executor = SingleThreadedExecutor()
    executor.add_node(no)
    threading.Thread(target=executor.spin, daemon=True).start()

    navegador = None
    try:
        if freio:
            log.warn('FREIO LIGADO: interpreta e registra, nada se move.')
        else:
            navegador = robo.criar_navegador()
            if not (robo.esperar_localizacao(navegador) and robo.esperar_servidores(navegador)):
                return 2
            log.warn('FREIO DESLIGADO: O ROBÔ VAI SE MOVER a cada pedido aceito.')
        try:
            perguntar_ao_ollama('ponto 1')   # carrega o modelo antes do primeiro pedido
        except Exception as erro:
            log.error(f'o modelo {MODELO} não respondeu ({type(erro).__name__}); '
                      '"pare" e dock/undock continuam atendidos.')
        while rclpy.ok():
            pronto.publish(Bool(data=True))
            try:
                frase = fila.get(timeout=0.5)
            except queue.Empty:
                continue
            pronto.publish(Bool(data=False))
            carga = bateria[0]
            if carga is None and freio:
                carga = 1.0   # sem robô: bateria simulada, só para ver a interpretação
            decisao = interpretar(frase, carga)
            texto = f'{frase!r} -> {resumo(decisao)} ({decisao["motivo"]})'
            if not decisao['permitido']:
                log.warn(f'RECUSADO: {texto}')
            elif freio:
                log.info(f'ACEITO: {texto} [freio: não executado]')
            else:
                log.info(f'ACEITO: {texto}')
                if decisao['acao'] != 'parar':   # parar: a meta já foi cancelada
                    executar(navegador, decisao, lambda: not fila.empty(), log)
        return 0
    except KeyboardInterrupt:
        if navegador is not None:
            navegador.cancelTask()
            log.warn('Encerrado; meta cancelada.')
        return 0
    finally:
        if navegador is not None:
            robo.encerrar(navegador)
        rclpy.try_shutdown()


if __name__ == '__main__':
    sys.exit(main())

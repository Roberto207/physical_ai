"""Exemplo: a camada de segurança entre a LLM e o robô, sem ROS e sem LLM.

A LLM só propõe uma ação em JSON. Este código decide se ela pode ser executada.
Nada do que o modelo escreve é executado como código.
"""
import math

BATERIA_MINIMA = 0.20
# Ações que levam o robô para longe da doca. Voltar, encaixar e parar valem com bateria baixa.
SAEM_DA_DOCA = {'ir_para', 'ir_para_coordenadas', 'sair_da_base'}
ARGUMENTOS = {'ir_para': {'local'}, 'ir_para_coordenadas': {'x', 'y', 'graus'},
              'voltar_para_base': set(), 'encaixar': set(), 'sair_da_base': set(), 'parar': set()}


def numero(valor):
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor))


def carga_valida(bateria):
    """Número de 0 a 1. O sensor_msgs/BatteryState usa NaN para "não medido"."""
    return numero(bateria) and 0 <= bateria <= 1


def validar(acao, locais, bateria, motivo_coordenada=None):
    """Devolve (True, '') se a ação pode rodar, ou (False, motivo) para explicar a recusa."""
    if not isinstance(acao, dict):
        return False, 'a resposta não é um objeto JSON'
    nome = acao.get('acao')
    argumentos = acao.get('argumentos', {})
    if not isinstance(nome, str) or nome not in ARGUMENTOS:
        return False, f'ação desconhecida: {nome!r}'
    if not isinstance(argumentos, dict) or set(argumentos) != ARGUMENTOS[nome]:
        return False, f'argumentos inválidos para {nome}'
    if nome == 'ir_para':
        if not isinstance(argumentos['local'], str) or argumentos['local'] not in locais:
            return False, f'não conheço o local {argumentos["local"]!r}'
    if nome == 'ir_para_coordenadas':
        x, y, graus = argumentos['x'], argumentos['y'], argumentos['graus']
        if not all(numero(v) for v in (x, y)) or not (graus is None or numero(graus)):
            return False, 'coordenadas precisam ser números'
        if motivo_coordenada is None:
            return False, 'não há mapa para conferir a coordenada'
        problema = motivo_coordenada(x, y)
        if problema:
            return False, f'coordenada ({x:g}, {y:g}) recusada: {problema}'
    if nome in SAEM_DA_DOCA and (not carga_valida(bateria) or bateria < BATERIA_MINIMA):
        return False, 'bateria insuficiente ou desconhecida para sair'
    return True, ''

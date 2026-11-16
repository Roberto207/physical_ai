"""Exemplo: a camada de segurança entre a LLM e o robô, sem ROS e sem LLM.

A LLM só propõe uma ação em JSON. Este código decide se ela pode ser executada.
Nada do que o modelo escreve é executado como código.
"""
BATERIA_MINIMA = 0.20
ARGUMENTOS = {'ir_para': {'local'}, 'voltar_para_base': set(), 'parar': set()}


def validar(acao, locais, bateria):
    """Devolve (True, '') se a ação pode rodar, ou (False, motivo) para explicar a recusa."""
    if not isinstance(acao, dict):
        return False, 'a resposta não é um objeto JSON'
    nome = acao.get('acao')
    argumentos = acao.get('argumentos', {})
    if nome not in ARGUMENTOS:
        return False, f'ação desconhecida: {nome!r}'
    if not isinstance(argumentos, dict) or set(argumentos) != ARGUMENTOS[nome]:
        return False, f'argumentos inválidos para {nome}'
    if nome == 'ir_para':
        if argumentos['local'] not in locais:
            return False, f'não conheço o local {argumentos["local"]!r}'
        if bateria is None or bateria < BATERIA_MINIMA:
            return False, 'bateria insuficiente ou desconhecida para sair'
    return True, ''

"""Pedido em português → uma ação validada do robô, com um LLM local (Ollama). Sem ROS.

O modelo não escreve código: responde um JSON {acao, local} restrito por esquema, que o código
confere antes de qualquer movimento. "pare", negação, sequência e dock/undock sozinhos são
decididos por regra, sem o modelo (o qwen2.5:1.5b errava esses casos nos ensaios de 25/11).
API: https://docs.ollama.com/api/chat · saída estruturada: https://docs.ollama.com/capabilities/structured-outputs

Teste sem robô:  python3 llm/interpretar.py "vá até a geladeira"
"""
import json
import math
import os
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

MODELO = os.environ.get('OLLAMA_MODELO', 'qwen2.5:1.5b')
URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434/api/chat')
TEMPO_LIMITE_S = 60
TAMANHO_MAXIMO = 200
BATERIA_MINIMA = 0.20
PROMPT = Path(__file__).with_name('prompt.txt')

# Nome → (número do ponto em robo.PONTOS, descrição que o modelo vê).
LOCAIS = {
    'ponto_1': (1, 'perto da doca e da impressora'),
    'ponto_2': (2, 'perto da geladeira (geladeirinha, frigobar) e do micro-ondas'),
    'ponto_3': (3, 'perto da porta'),
    'ponto_4': (4, 'perto da janela e da mesa central'),
}
ACOES = ('ir_para', 'voltar_para_base', 'encaixar', 'sair_da_base', 'parar', 'nenhuma')
SAEM_DA_DOCA = {'ir_para', 'sair_da_base'}   # exigem bateria; voltar, encaixar e parar não

# ---- Parar: decidido sem o modelo, porque não pode depender de ele acertar nem demorar.
# Errar para o lado de parar é aceitável; deixar de reconhecer um pedido de parar não é.
PARAR_EM_QUALQUER_LUGAR = re.compile(
    r'\b(pare|parem|parar|parou|stop|halt|freeze|abort|aborte|aborta|abortar|cancel|cancela|cancele'
    r'|cancelar|interrompa|interrompe|interromper|suspenda|suspende|suspender|aguarde|aguarda'
    r'|emergencia|socorro|freie|freia|frear|basta|vai bater|don t move|hold on|hold it)\b'
    r'|\b(para|chega) de (andar|se mover|se mexer|ir|navegar)\b'
    r'|\b(fica|fique|ficar) (\w+ )?(parado|quieto|ai|onde (voce )?esta)\b'
    r'|\b(desliga|desligue|encerra|encerre|termina|termine) (o |a )?(motor|movimento|navegacao)\b'
    r'|\bnao (se )?(mexa|mexe|mova|move|anda|ande|continue|continua|prossiga|siga)\b'
    r'|\bnao (va|vai) mais\b'
    r'|^cuidado\b|\bcuidado$')
# Só são ordem de parar quando a frase não diz mais nada ("espera aí", mas não "chega perto
# da porta"; "para o robô", mas não "vá para a porta").
SO_PARAR = {'para', 'pra', 'chega', 'espera', 'espere', 'wait', 'alto', 'calma', 'parado', 'quieto',
            'segura', 'congela', 'trava', 'desiste', 'paralisa', 'cuidado'}
ENCHIMENTO = {'o', 'robo', 'ei', 'oh', 'ow', 'opa', 'mano', 'ai', 'aqui', 'la', 'por', 'favor',
              'agora', 'ja', 'logo', 'so', 'imediatamente', 'tudo', 'isso', 'com', 'pode', 'um',
              'pouco', 'deu'}
# "dock" e "undock" são os comandos do tutorial oficial, e o modelo troca um pelo outro.
SO_DOCK = {
    'sair_da_base': re.compile(r'^(faca |faz |fazer |pode fazer )?(o )?(undock|desencaix\w*)'
                               r'( (o robo|da (doca|base)))?$'),
    'encaixar': re.compile(r'^(faca |faz |fazer |pode fazer )?(o )?(dock|encaix\w*)'
                           r'( (o robo|na (doca|base)))?$'),
}
NEGACAO = re.compile(r'\b(nao|nunca|jamais|nem)\b')
# Uma ordem por vez: o modelo tende a reduzir uma sequência de destinos ao primeiro.
SEQUENCIA = re.compile(r'\b(depois|em seguida|pontos)\b|\bponto\b.*\bponto\b')


def normalizar(texto):
    sem_acento = unicodedata.normalize('NFKD', texto.casefold())
    # Fora os acentos e os caracteres invisíveis (categoria Cf), que quebrariam as palavras.
    sem_acento = ''.join(c for c in sem_acento
                         if not unicodedata.combining(c) and unicodedata.category(c) != 'Cf')
    limpo = ' '.join(re.sub(r'[^\w\s]', ' ', sem_acento).split())
    return re.sub(r'([a-z])\1{2,}', r'\1', limpo)   # "paraaa" -> "para"


def pede_para_parar(texto):
    """Recebe o texto já normalizado."""
    if PARAR_EM_QUALQUER_LUGAR.search(texto):
        return True
    principais = [palavra for palavra in texto.split() if palavra not in ENCHIMENTO]
    return bool(principais) and all(palavra in SO_PARAR for palavra in principais)


def esquema():
    return {
        'type': 'object',
        'properties': {'acao': {'type': 'string', 'enum': list(ACOES)},
                       'local': {'type': 'string', 'enum': [*LOCAIS, 'nenhum']}},
        'required': ['acao', 'local'],
    }


def montar_prompt():
    locais = '\n'.join(f'- {nome}: {descricao}' for nome, (_, descricao) in LOCAIS.items())
    return PROMPT.read_text(encoding='utf-8').format(
        locais=locais, esquema=json.dumps(esquema(), ensure_ascii=False))


def perguntar_ao_ollama(frase):
    """Devolve o dicionário que o modelo respondeu. Qualquer falha vira exceção."""
    corpo = {
        'model': MODELO,
        'messages': [{'role': 'system', 'content': montar_prompt()},
                     {'role': 'user', 'content': f'Pedido: {frase}'}],
        'format': esquema(),
        'stream': False,
        'keep_alive': '30m',     # mantém o modelo na memória entre os pedidos
        'options': {'temperature': 0, 'seed': 0, 'num_predict': 64},
    }
    pedido = urllib.request.Request(URL, data=json.dumps(corpo).encode(),
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
        return json.loads(json.load(resposta)['message']['content'])


def carga_valida(bateria):
    """Número de 0 a 1. O BatteryState usa NaN para "não medido"."""
    return (isinstance(bateria, (int, float)) and not isinstance(bateria, bool)
            and math.isfinite(bateria) and 0 <= bateria <= 1)


def decidir(acao, local, bateria, motivo):
    """Confere a ação; devolve {'permitido', 'acao', 'local', 'motivo'}."""
    if acao not in ACOES or acao == 'nenhuma':
        return recusa('o modelo não reconheceu um comando')
    if acao == 'ir_para' and local not in LOCAIS:
        return recusa(f'não conheço o local {local!r}')
    if acao in SAEM_DA_DOCA and (not carga_valida(bateria) or bateria < BATERIA_MINIMA):
        return recusa('bateria insuficiente ou desconhecida para sair')
    return {'permitido': True, 'acao': acao,
            'local': local if acao == 'ir_para' else None, 'motivo': motivo}


def recusa(motivo):
    return {'permitido': False, 'acao': None, 'local': None, 'motivo': motivo}


def interpretar(frase, bateria, consultar=perguntar_ao_ollama):
    """Na dúvida ou em erro, recusa. `consultar` é trocado por um falso nos testes."""
    if not isinstance(frase, str):
        return recusa('o pedido não é um texto')
    texto = normalizar(frase)
    if pede_para_parar(texto):     # vale mesmo em mensagem longa
        return {'permitido': True, 'acao': 'parar', 'local': None, 'motivo': 'regra de parar'}
    if not texto or len(frase) > TAMANHO_MAXIMO:
        return recusa('pedido vazio ou longo demais')
    if NEGACAO.search(texto):
        return recusa('pedido com negação')
    if SEQUENCIA.search(texto):
        return recusa('mais de um destino: peça um de cada vez')
    for acao, padrao in SO_DOCK.items():
        if padrao.search(texto):
            return decidir(acao, None, bateria, 'regra de dock/undock')
    try:
        resposta = consultar(frase)
        acao, local = resposta['acao'], resposta['local']
        if not isinstance(acao, str) or not isinstance(local, str):
            raise TypeError('acao e local precisam ser texto')
    except Exception as erro:   # rede, tempo esgotado, JSON quebrado, campo faltando
        return recusa(f'falha ao consultar o modelo: {type(erro).__name__}')
    return decidir(acao, local, bateria, 'modelo')


def resumo(decisao):
    """'ir_para:ponto_2', 'voltar_para_base', 'parar' ou 'recusar'."""
    if not decisao['permitido']:
        return 'recusar'
    return f'{decisao["acao"]}:{decisao["local"]}' if decisao['local'] else decisao['acao']


if __name__ == '__main__':
    print(json.dumps(interpretar(' '.join(sys.argv[1:]), 1.0), ensure_ascii=False, indent=2))

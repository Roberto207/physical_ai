"""Traduz um pedido em português para uma ação validada do robô, com um LLM local (Ollama).

Python puro, sem ROS e sem bibliotecas externas: nada aqui move o robô. Segue o desenho do
exemplo oficial natural_language_nav (turtlebot4_tutorials, ramo humble): texto de entrada,
prompt em arquivo, lista de destinos. Duas diferenças: o modelo é local, e a resposta é um JSON
restrito por esquema que passa pelo validar_acao.py, em vez de código executado com exec().
API do Ollama: https://docs.ollama.com/api/chat
Saída estruturada: https://docs.ollama.com/capabilities/structured-outputs

Uso (na pasta do pacote): python3 -m llm_tb4.interpretador "vá até a geladeirinha"
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

from llm_tb4 import mapa, recursos
from llm_tb4.coordenadas import ler_coordenadas, ler_direcao
from llm_tb4.validar_acao import validar

MODELO = os.environ.get('OLLAMA_MODELO', 'qwen2.5:1.5b')
URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434/api/chat')
TEMPO_LIMITE_S = 60
TAMANHO_MAXIMO = 200
# ---- Ordem de parar: decidida sem o modelo, porque não pode depender de ele acertar nem demorar.
# Errar para o lado de parar é aceitável; deixar de reconhecer um pedido de parar não é.
# Vale em qualquer posição da frase:
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
# Palavras que só são ordem de parar quando a frase não diz mais nada ("espera aí", mas não
# "chega perto da porta"; "para o robô", mas não "vá para a porta").
SO_PARAR = {'para', 'pra', 'chega', 'espera', 'espere', 'wait', 'alto', 'calma', 'parado', 'quieto',
            'segura', 'congela', 'trava', 'desiste', 'paralisa', 'cuidado'}
ENCHIMENTO = {'o', 'robo', 'ei', 'oh', 'ow', 'opa', 'mano', 'ai', 'aqui', 'la', 'por', 'favor',
              'agora', 'ja', 'logo', 'so', 'imediatamente', 'tudo', 'isso', 'com', 'pode', 'um',
              'pouco', 'deu'}
# "dock" e "undock" são os comandos do tutorial oficial, e o modelo troca um pelo outro: quando o
# pedido é só isso, o código decide. Texto já normalizado.
SO_DOCK = {
    'sair_da_base': re.compile(r'^(faca |faz |fazer |pode fazer )?(o )?(undock|desencaix\w*)'
                               r'( (o robo|da (doca|base)))?$'),
    'encaixar': re.compile(r'^(faca |faz |fazer |pode fazer )?(o )?(dock|encaix\w*)'
                           r'( (o robo|na (doca|base)))?$'),
}
NEGACAO = re.compile(r'\b(nao|nunca|jamais|nem)\b')
# Uma ordem por vez: sequência de destinos, que o modelo tende a reduzir ao primeiro.
SEQUENCIA = re.compile(r'\b(depois|em seguida|pontos)\b|\bponto\b.*\bponto\b')


def carregar_destinos(caminho=None):
    caminho = caminho or recursos.caminho('config', 'destinos.json')
    return json.loads(Path(caminho).read_text(encoding='utf-8'))


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


def esquema(destinos):
    return {
        'type': 'object',
        'properties': {
            'acao': {'type': 'string',
                     'enum': ['ir_para', 'ir_para_coordenadas', 'voltar_para_base',
                              'encaixar', 'sair_da_base', 'parar', 'nenhuma']},
            'local': {'type': 'string', 'enum': [*destinos, 'nenhum']},
        },
        'required': ['acao', 'local'],
    }


def montar_prompt(destinos):
    modelo = recursos.caminho('prompts', 'comandos.txt').read_text(encoding='utf-8')
    locais = '\n'.join(f'- {nome}: {d["descricao"]}' for nome, d in destinos.items())
    return modelo.format(locais=locais, esquema=json.dumps(esquema(destinos), ensure_ascii=False))


def perguntar_ao_ollama(frase, destinos, modelo=None, url=None):
    """Devolve o dicionário que o modelo respondeu. Qualquer falha vira exceção."""
    corpo = {
        'model': modelo or MODELO,
        'messages': [{'role': 'system', 'content': montar_prompt(destinos)},
                     {'role': 'user', 'content': f'Pedido: {frase}'}],
        'format': esquema(destinos),
        'stream': False,
        'keep_alive': '30m',     # mantém o modelo na memória entre os pedidos
        'options': {'temperature': 0, 'seed': 0, 'num_predict': 64},
    }
    pedido = urllib.request.Request(url or URL, data=json.dumps(corpo).encode(),
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
        return json.loads(json.load(resposta)['message']['content'])


def recusa(motivo, falha_modelo=False):
    decisao = {'permitido': False, 'acao': None, 'motivo': motivo}
    if falha_modelo:
        decisao['falha_modelo'] = True
    return decisao


def interpretar(frase, destinos, bateria, consultar=perguntar_ao_ollama,
                motivo_coordenada=None):
    """Devolve {'permitido', 'acao', 'motivo'}. Na dúvida ou em erro, recusa."""
    if not isinstance(frase, str):
        return recusa('o pedido não é um texto')
    texto = normalizar(frase)
    # Primeiro de tudo: parar vale mesmo em mensagem longa ou repetida.
    if pede_para_parar(texto):
        return {'permitido': True, 'acao': {'acao': 'parar', 'argumentos': {}},
                'motivo': 'ordem de parar (sem consultar o modelo)'}
    if not texto or len(frase) > TAMANHO_MAXIMO:
        return recusa('pedido vazio ou longo demais')
    if NEGACAO.search(texto):
        return recusa('pedido com negação')
    if SEQUENCIA.search(texto):
        return recusa('mais de um destino: peça um de cada vez')
    for nome, padrao in SO_DOCK.items():
        if padrao.search(texto):
            acao = {'acao': nome, 'argumentos': {}}
            permitido, motivo = validar(acao, destinos, bateria)
            return {'permitido': permitido, 'acao': acao if permitido else None, 'motivo': motivo}
    try:
        resposta = consultar(frase, destinos)
        nome, local = resposta['acao'], resposta['local']
        if not isinstance(nome, str) or not isinstance(local, str):
            raise TypeError('acao e local precisam ser texto')
    except Exception as erro:   # rede, tempo esgotado, JSON quebrado, campo faltando ou errado
        return recusa(f'falha ao consultar o modelo: {type(erro).__name__}', falha_modelo=True)
    if nome == 'nenhuma':
        return recusa('o modelo não reconheceu um comando')
    argumentos = {'local': local} if nome == 'ir_para' else {}
    if nome == 'ir_para_coordenadas':
        ponto = ler_coordenadas(frase)   # os números vêm do pedido, nunca do modelo
        if ponto is None:
            return recusa('não li duas coordenadas sem ambiguidade (use "x -1 y 0")')
        argumentos = {'x': ponto[0], 'y': ponto[1], 'graus': ler_direcao(frase)}
    acao = {'acao': nome, 'argumentos': argumentos}
    permitido, motivo = validar(acao, destinos, bateria, motivo_coordenada)
    return {'permitido': permitido, 'acao': acao if permitido else None, 'motivo': motivo}


def resumo(decisao):
    """'ir_para:ponto_2', 'voltar_para_base', 'parar' ou 'recusar'."""
    if not decisao['permitido']:
        return 'recusar'
    acao = decisao['acao']
    if acao['acao'] == 'ir_para_coordenadas':
        x, y = acao['argumentos']['x'], acao['argumentos']['y']
        return f'ir_para_coordenadas:{x:g},{y:g}'
    local = acao['argumentos'].get('local')
    return f'{acao["acao"]}:{local}' if local else acao['acao']


def main():
    argumentos = argparse.ArgumentParser(description='Interpreta um pedido (não move o robô)')
    argumentos.add_argument('frase')
    argumentos.add_argument('--bateria', type=float, default=1.0,
                            help='carga de 0 a 1 usada na validação (simulada; padrão 1.0)')
    argumentos.add_argument('--mapa', default=None, help='mapa para conferir coordenadas')
    opcoes = argumentos.parse_args()
    arquivo = opcoes.mapa or Path(__file__).resolve().parents[4] / 'mapas' / 'mapa_lab_novo.yaml'
    decisao = interpretar(opcoes.frase, carregar_destinos(), opcoes.bateria,
                          motivo_coordenada=mapa.verificador(arquivo))
    print(json.dumps(decisao, ensure_ascii=False, indent=2))
    return 0 if decisao['permitido'] else 1


if __name__ == '__main__':
    sys.exit(main())

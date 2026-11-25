"""Traduz um pedido em português para uma ação validada do robô, com um LLM local (Ollama).

Python puro, sem ROS e sem bibliotecas externas: nada aqui move o robô. Segue o desenho do
exemplo oficial natural_language_nav (turtlebot4_tutorials, ramo humble): texto de entrada,
prompt em arquivo, lista de destinos. Duas diferenças: o modelo é local, e a resposta é um JSON
restrito por esquema que passa pelo validar_acao.py, em vez de código executado com exec().
API do Ollama: https://docs.ollama.com/api/chat
Saída estruturada: https://docs.ollama.com/capabilities/structured-outputs

Uso: python3 interpretador.py "vá até a geladeirinha"
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

from validar_acao import validar

PASTA = Path(__file__).resolve().parent
MODELO = os.environ.get('OLLAMA_MODELO', 'qwen2.5:1.5b')
URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434/api/chat')
TEMPO_LIMITE_S = 60
TAMANHO_MAXIMO = 200
# Decididas sem o modelo. "parar" é o pedido que não pode depender de ele acertar nem demorar.
# "para" só vale como ordem quando abre a frase ("para tudo"), não como preposição.
ORDEM_DE_PARAR = re.compile(r'\b(pare|parar|stop|cancele|cancela|cancelar|interrompa)\b'
                            r'|^para( tudo| agora| ai|$)')
NEGACAO = re.compile(r'\b(nao|nunca|jamais|nem)\b')
# Uma ordem por vez: sequência de destinos, que o modelo tende a reduzir ao primeiro.
SEQUENCIA = re.compile(r'\b(depois|em seguida|pontos)\b|\bponto\b.*\bponto\b')


def carregar_destinos(caminho=PASTA / 'destinos.json'):
    return json.loads(Path(caminho).read_text(encoding='utf-8'))


def normalizar(texto):
    sem_acento = unicodedata.normalize('NFKD', texto.casefold())
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^\w\s]', ' ', sem_acento).split())


def esquema(destinos):
    return {
        'type': 'object',
        'properties': {
            'acao': {'type': 'string',
                     'enum': ['ir_para', 'voltar_para_base', 'parar', 'nenhuma']},
            'local': {'type': 'string', 'enum': [*destinos, 'nenhum']},
        },
        'required': ['acao', 'local'],
    }


def montar_prompt(destinos):
    modelo = (PASTA / 'prompts' / 'comandos.txt').read_text(encoding='utf-8')
    locais = '\n'.join(f'- {nome}: {d["descricao"]}' for nome, d in destinos.items())
    return modelo.format(locais=locais, esquema=json.dumps(esquema(destinos), ensure_ascii=False))


def perguntar_ao_ollama(frase, destinos):
    """Devolve o dicionário que o modelo respondeu. Qualquer falha vira exceção."""
    corpo = {
        'model': MODELO,
        'messages': [{'role': 'system', 'content': montar_prompt(destinos)},
                     {'role': 'user', 'content': f'Pedido: {frase}'}],
        'format': esquema(destinos),
        'stream': False,
        'keep_alive': '30m',     # mantém o modelo na memória entre os pedidos
        'options': {'temperature': 0, 'seed': 0, 'num_predict': 64},
    }
    pedido = urllib.request.Request(URL, data=json.dumps(corpo).encode(),
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
        return json.loads(json.load(resposta)['message']['content'])


def recusa(motivo):
    return {'permitido': False, 'acao': None, 'motivo': motivo}


def interpretar(frase, destinos, bateria, consultar=perguntar_ao_ollama):
    """Devolve {'permitido', 'acao', 'motivo'}. Na dúvida ou em erro, recusa."""
    texto = normalizar(frase)
    if not texto or len(frase) > TAMANHO_MAXIMO:
        return recusa('pedido vazio ou longo demais')
    if ORDEM_DE_PARAR.search(texto):
        return {'permitido': True, 'acao': {'acao': 'parar', 'argumentos': {}},
                'motivo': 'ordem de parar (sem consultar o modelo)'}
    if NEGACAO.search(texto):
        return recusa('pedido com negação')
    if SEQUENCIA.search(texto):
        return recusa('mais de um destino: peça um de cada vez')
    try:
        resposta = consultar(frase, destinos)
        nome, local = resposta['acao'], resposta['local']
    except Exception as erro:   # rede, tempo esgotado, JSON quebrado, campo faltando
        return recusa(f'falha ao consultar o modelo: {type(erro).__name__}')
    if nome == 'nenhuma':
        return recusa('o modelo não reconheceu um comando')
    acao = {'acao': nome, 'argumentos': {'local': local} if nome == 'ir_para' else {}}
    permitido, motivo = validar(acao, destinos, bateria)
    return {'permitido': permitido, 'acao': acao if permitido else None, 'motivo': motivo}


def resumo(decisao):
    """'ir_para:ponto_2', 'voltar_para_base', 'parar' ou 'recusar'."""
    if not decisao['permitido']:
        return 'recusar'
    acao = decisao['acao']
    local = acao['argumentos'].get('local')
    return f'{acao["acao"]}:{local}' if local else acao['acao']


def main():
    argumentos = argparse.ArgumentParser(description='Interpreta um pedido (não move o robô)')
    argumentos.add_argument('frase')
    argumentos.add_argument('--bateria', type=float, default=1.0,
                            help='carga de 0 a 1 usada na validação (simulada; padrão 1.0)')
    opcoes = argumentos.parse_args()
    decisao = interpretar(opcoes.frase, carregar_destinos(), opcoes.bateria)
    print(json.dumps(decisao, ensure_ascii=False, indent=2))
    return 0 if decisao['permitido'] else 1


if __name__ == '__main__':
    sys.exit(main())

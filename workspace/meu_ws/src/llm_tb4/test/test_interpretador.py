"""L0 do interpretador, com um modelo de mentira: não precisa do Ollama nem do ROS."""
import json
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from llm_tb4 import interpretador, recursos
from llm_tb4.interpretador import (carregar_destinos, esquema, interpretar, montar_prompt,
                                   perguntar_ao_ollama, resumo)

DESTINOS = carregar_destinos()


def modelo_que_responde(acao, local='nenhum'):
    return lambda frase, destinos: {'acao': acao, 'local': local}


def modelo_proibido(frase, destinos):
    # pytest.fail não é capturado pelo "except Exception" do interpretar; AssertionError seria.
    pytest.fail('o modelo não devia ser consultado')


PEDIDOS_DE_PARAR = [
    'Pare', 'para tudo', 'CANCELE o movimento', 'não pare... pare!', 'robô, para!', 'para o robô',
    'ô robô, para aí', 'Para! Para! Para!', 'ei, para', 'para já', 'para de andar', 'paraaa',
    'pra tudo', 'parem', 'pode parar', 'chega!', 'chega de ir na porta', 'espera aí', 'aguarde',
    'alto!', 'calma, calma', 'basta', 'aborta a missão', 'interrompa a navegação', 'fica parado',
    'fique parado', 'fica aí', 'fica onde está', 'parado!', 'não se mexa', 'não anda mais',
    'não continue', 'não vá mais', 'socorro, vai bater!', 'cuidado!', 'emergência!',
    'stop moving', "don't move", 'hold on', 'cancel the mission', 'desliga o motor',
    'pare! ' * 40, 'x' * 500 + ' pare', 'pa\u200bre']


@pytest.mark.parametrize('frase', PEDIDOS_DE_PARAR)
def test_parar_nao_depende_do_modelo(frase):
    assert resumo(interpretar(frase, DESTINOS, None, modelo_proibido)) == 'parar'


@pytest.mark.parametrize('frase', [
    'vá para a porta', 'vai pra janela', 'pode ir para o ponto 2', 'vá para lá',
    'chega perto da impressora', 'chega mais perto da porta', 'vá com cuidado até a porta',
    'volte para a doca', 'quero ir para a geladeira', 'vai para o robô da porta',
    'fique perto da janela', 'vá até a parede'])
def test_pedido_comum_nao_vira_parar(frase):
    assert not interpretador.pede_para_parar(interpretador.normalizar(frase))


@pytest.mark.parametrize('frase, motivo', [
    ('', 'vazio'), ('   ', 'vazio'), ('x' * 500, 'longo'), ('Não vá ao ponto 2', 'negação'),
    ('nunca volte à doca', 'negação'), ('Vá ao ponto 1 e depois ao ponto 3', 'destino'),
    ('passe pelos pontos 1 e 2', 'destino'), ('ponto 1 ou ponto 2', 'destino'),
    (None, 'texto'), (b'ponto 1', 'texto')])
def test_recusa_antes_do_modelo(frase, motivo):
    decisao = interpretar(frase, DESTINOS, 1.0, modelo_proibido)
    assert resumo(decisao) == 'recusar' and motivo in decisao['motivo']


def test_preposicao_para_nao_e_ordem_de_parar():
    decisao = interpretar('vá para o ponto 2', DESTINOS, 1.0,
                          modelo_que_responde('ir_para', 'ponto_2'))
    assert resumo(decisao) == 'ir_para:ponto_2'


@pytest.mark.parametrize('resposta, bateria', [
    ({'acao': 'ir_para', 'local': 'marte'}, 1.0),
    ({'acao': 'ir_para', 'local': 'nenhum'}, 1.0),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, 0.1),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, None),
    ({'acao': 'exec', 'local': 'nenhum'}, 1.0),
    ({'acao': 'nenhuma', 'local': 'ponto_1'}, 1.0),
    ({'acao': 'ir_para'}, 1.0),
    ({'acao': ['ir_para'], 'local': 'ponto_1'}, 1.0),
    ({'acao': 'ir_para', 'local': ['ponto_1']}, 1.0),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, float('nan')),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, float('inf')),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, 15),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, True),
    ({'acao': 'ir_para', 'local': 'ponto_1'}, '0.9'),
    ('import os', 1.0),
    (None, 1.0),
])
def test_resposta_invalida_do_modelo_nao_move(resposta, bateria):
    decisao = interpretar('vá até lá', DESTINOS, bateria, lambda f, d: resposta)
    assert resumo(decisao) == 'recusar'


@pytest.mark.parametrize('resposta', [
    {'acao': ['ir_para'], 'local': 'ponto_1'}, {'acao': 'ir_para', 'local': None}])
def test_tipo_errado_na_resposta_conta_como_falha_do_modelo(resposta):
    decisao = interpretar('vá ao ponto 1', DESTINOS, 1.0, lambda f, d: resposta)
    assert resumo(decisao) == 'recusar' and decisao['falha_modelo']


@pytest.mark.parametrize('erro', [urllib.error.URLError('x'), TimeoutError(),
                                  json.JSONDecodeError('x', 'y', 0)])
def test_falha_do_modelo_nao_move(erro):
    def falha(frase, destinos):
        raise erro
    assert resumo(interpretar('vá ao ponto 1', DESTINOS, 1.0, falha)) == 'recusar'


def test_voltar_para_base_vale_com_bateria_baixa():
    decisao = interpretar('volte', DESTINOS, 0.05, modelo_que_responde('voltar_para_base'))
    assert resumo(decisao) == 'voltar_para_base'


def test_prompt_lista_os_destinos_e_o_esquema():
    texto = montar_prompt(DESTINOS)
    assert all(nome in texto for nome in DESTINOS)
    assert esquema(DESTINOS)['properties']['local']['enum'] == [*DESTINOS, 'nenhum']
    assert '"required"' in texto and '{locais}' not in texto


@pytest.fixture
def ollama_falso(monkeypatch):
    """Servidor local no lugar do Ollama: guarda o pedido e devolve o que o teste mandar."""
    estado = {'pedido': None, 'conteudo': '{"acao": "ir_para", "local": "ponto_3"}'}

    class Resposta(BaseHTTPRequestHandler):
        def do_POST(self):
            corpo = self.rfile.read(int(self.headers['Content-Length']))
            estado['pedido'] = json.loads(corpo)
            saida = json.dumps({'message': {'content': estado['conteudo']}}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(saida)

        def log_message(self, *args):
            pass

    servidor = HTTPServer(('127.0.0.1', 0), Resposta)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    monkeypatch.setattr(interpretador, 'URL', f'http://127.0.0.1:{servidor.server_port}/api/chat')
    monkeypatch.delenv('http_proxy', raising=False)
    yield estado
    servidor.shutdown()


def test_pedido_ao_modelo_segue_a_api_do_ollama(ollama_falso):
    resposta = perguntar_ao_ollama('vá até a porta', DESTINOS)
    assert resposta == {'acao': 'ir_para', 'local': 'ponto_3'}
    pedido = ollama_falso['pedido']
    assert pedido['model'] == interpretador.MODELO
    assert pedido['format'] == esquema(DESTINOS)
    assert pedido['stream'] is False
    assert pedido['options']['temperature'] == 0
    assert [m['role'] for m in pedido['messages']] == ['system', 'user']
    assert 'vá até a porta' in pedido['messages'][1]['content']
    assert pedido['messages'][0]['content'] == montar_prompt(DESTINOS)


@pytest.mark.parametrize('conteudo', ['isto não é JSON', '[]', '"texto"', '{}'])
def test_resposta_quebrada_do_servidor_vira_falha(ollama_falso, conteudo):
    ollama_falso['conteudo'] = conteudo
    decisao = interpretar('vá até a porta', DESTINOS, 1.0)
    assert resumo(decisao) == 'recusar' and decisao['falha_modelo']


def test_destinos_apontam_para_os_quatro_pontos_da_patrulha():
    assert sorted(d['ponto'] for d in DESTINOS.values()) == [1, 2, 3, 4]


@pytest.mark.parametrize('arquivo', sorted(recursos.caminho('test', 'frases').glob('*.json')))
def test_casos_de_frases_citam_destinos_que_existem(arquivo):
    for caso in json.loads(arquivo.read_text(encoding='utf-8')):
        esperado = caso['esperado']
        for aceito in esperado.split('|'):
            if aceito.startswith('ir_para_coordenadas:'):
                assert len(aceito.split(':')[1].split(',')) == 2
            elif aceito.startswith('ir_para:'):
                assert aceito.split(':')[1] in DESTINOS
            else:
                assert aceito in ('recusar', 'parar', 'voltar_para_base', 'encaixar',
                                  'sair_da_base')

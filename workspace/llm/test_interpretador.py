"""L0 do interpretador, com um modelo de mentira: não precisa do Ollama nem do ROS."""
import json
import urllib.error

import pytest

from interpretador import (PASTA, carregar_destinos, esquema, interpretar, montar_prompt, resumo)

DESTINOS = carregar_destinos()


def modelo_que_responde(acao, local='nenhum'):
    return lambda frase, destinos: {'acao': acao, 'local': local}


def modelo_proibido(frase, destinos):
    raise AssertionError('o modelo não devia ser consultado')


@pytest.mark.parametrize('frase', ['Pare', 'para tudo', 'CANCELE o movimento', 'não pare... pare!'])
def test_parar_nao_depende_do_modelo(frase):
    assert resumo(interpretar(frase, DESTINOS, None, modelo_proibido)) == 'parar'


@pytest.mark.parametrize('frase', [
    '', '   ', 'x' * 500, 'Não vá ao ponto 2', 'nunca volte à doca',
    'Vá ao ponto 1 e depois ao ponto 3', 'passe pelos pontos 1 e 2', 'ponto 1 ou ponto 2'])
def test_recusa_antes_do_modelo(frase):
    assert resumo(interpretar(frase, DESTINOS, 1.0, modelo_proibido)) == 'recusar'


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
    ('import os', 1.0),
    (None, 1.0),
])
def test_resposta_invalida_do_modelo_nao_move(resposta, bateria):
    decisao = interpretar('vá até lá', DESTINOS, bateria, lambda f, d: resposta)
    assert resumo(decisao) == 'recusar'


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


def test_destinos_apontam_para_os_quatro_pontos_da_patrulha():
    assert sorted(d['ponto'] for d in DESTINOS.values()) == [1, 2, 3, 4]


@pytest.mark.parametrize('arquivo', sorted((PASTA / 'testes_frases').glob('*.json')))
def test_casos_de_frases_citam_destinos_que_existem(arquivo):
    for caso in json.loads(arquivo.read_text(encoding='utf-8')):
        esperado = caso['esperado']
        if esperado.startswith('ir_para:'):
            assert esperado.split(':')[1] in DESTINOS
        else:
            assert esperado in ('recusar', 'parar', 'voltar_para_base')

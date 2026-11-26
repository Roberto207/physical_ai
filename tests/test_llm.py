"""Parte pura do LLM e da patrulha, com um modelo de mentira: sem Ollama e sem ROS."""
import ast
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'llm'))
from interpretar import ACOES, LOCAIS, interpretar, montar_prompt, resumo  # noqa: E402


def modelo(acao, local='nenhum'):
    return lambda frase: {'acao': acao, 'local': local}


def modelo_proibido(frase):
    pytest.fail('o modelo não devia ser consultado')   # não é capturado pelo interpretar


@pytest.mark.parametrize('frase', [
    'Pare', 'para tudo', 'CANCELE o movimento', 'robô, para!', 'para o robô', 'paraaa',
    'chega!', 'espera aí', 'fica parado', 'não se mexa', 'não vá mais', 'socorro, vai bater!',
    'stop moving', "don't move", 'desliga o motor', 'pare! ' * 40, 'x' * 500 + ' pare',
    'pa​re'])
def test_parar_nao_depende_do_modelo(frase):
    assert resumo(interpretar(frase, None, modelo_proibido)) == 'parar'


@pytest.mark.parametrize('frase', [
    'vá para a porta', 'vai pra janela', 'chega perto da impressora', 'vá com cuidado até a porta',
    'volte para a doca', 'fique perto da janela'])
def test_pedido_comum_nao_vira_parar(frase):
    assert resumo(interpretar(frase, 1.0, modelo('nenhuma'))) != 'parar'


@pytest.mark.parametrize('frase, motivo', [
    ('', 'vazio'), ('x' * 500, 'longo'), ('Não vá ao ponto 2', 'negação'),
    ('Vá ao ponto 1 e depois ao ponto 3', 'destino'), ('passe pelos pontos 1 e 2', 'destino'),
    (None, 'texto')])
def test_recusa_antes_do_modelo(frase, motivo):
    decisao = interpretar(frase, 1.0, modelo_proibido)
    assert resumo(decisao) == 'recusar' and motivo in decisao['motivo']


@pytest.mark.parametrize('frase, esperado', [
    ('undock', 'sair_da_base'), ('faça o dock', 'encaixar'), ('encaixe na doca', 'encaixar')])
def test_dock_e_undock_sao_regra(frase, esperado):
    assert resumo(interpretar(frase, 1.0, modelo_proibido)) == esperado


@pytest.mark.parametrize('resposta, esperado', [
    ({'acao': 'ir_para', 'local': 'ponto_2'}, 'ir_para:ponto_2'),
    ({'acao': 'voltar_para_base', 'local': 'nenhum'}, 'voltar_para_base'),
    ({'acao': 'ir_para', 'local': 'cozinha'}, 'recusar'),
    ({'acao': 'nenhuma', 'local': 'nenhum'}, 'recusar'),
    ({'acao': 'voar', 'local': 'nenhum'}, 'recusar'),
    ({'acao': 'ir_para', 'local': ['ponto_1']}, 'recusar'),
    ({'acao': 'ir_para'}, 'recusar'),
    ('não é um objeto', 'recusar')])
def test_resposta_do_modelo_e_conferida(resposta, esperado):
    assert resumo(interpretar('vá até a geladeira', 1.0, lambda f: resposta)) == esperado


@pytest.mark.parametrize('bateria', [None, float('nan'), 0.1, 2.0, True])
def test_sem_bateria_nao_sai_mas_volta(bateria):
    assert resumo(interpretar('vá à janela', bateria, modelo('ir_para', 'ponto_4'))) == 'recusar'
    assert resumo(interpretar('undock', bateria, modelo_proibido)) == 'recusar'
    voltar = interpretar('volte para a base', bateria, modelo('voltar_para_base'))
    assert resumo(voltar) == 'voltar_para_base'


def test_falha_do_modelo_recusa():
    def quebrado(frase):
        raise TimeoutError
    decisao = interpretar('vá até a porta', 1.0, quebrado)
    assert resumo(decisao) == 'recusar' and decisao['motivo'].startswith('falha ao consultar')


def test_prompt_lista_os_locais_e_as_acoes():
    prompt = montar_prompt()
    assert all(nome in prompt for nome in LOCAIS)
    assert all(f'"{acao}"' in prompt for acao in ACOES)


def test_frases_de_avaliacao_usam_resultados_que_existem():
    for caso in json.loads((RAIZ / 'llm' / 'frases.json').read_text(encoding='utf-8')):
        for aceito in caso['esperado'].split('|'):
            acao, _, local = aceito.partition(':')
            assert acao in (*ACOES, 'recusar') and (not local or local in LOCAIS), caso


def test_pontos_iguais_aos_da_task1():
    """Os valores medidos não podem mudar sem querer (patrol_loop.py da tag task1-concluida)."""
    corpo = ast.parse((RAIZ / 'robo.py').read_text(encoding='utf-8')).body
    valores = {n.targets[0].id: ast.literal_eval(n.value) for n in corpo
               if isinstance(n, ast.Assign)
               and getattr(n.targets[0], 'id', '') in ('DOCA', 'PONTOS')}
    assert valores['DOCA'] == (-0.2025940716266632, 0.10048891603946686)
    assert valores['PONTOS'] == (
        (-0.5858250856399536, -0.8073815107345581), (-3.549771785736084, -3.0633668899536133),
        (-5.608144283294678, -0.8229406476020813), (-1.9671252965927124, 1.0304899215698242))
    assert sorted(numero for numero, _ in LOCAIS.values()) == [1, 2, 3, 4]

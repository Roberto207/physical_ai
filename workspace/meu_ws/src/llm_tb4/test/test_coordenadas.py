"""Coordenadas livres: leitura por código, validação no mapa e comandos dock/undock."""
import json
from pathlib import Path

import pytest

from llm_tb4 import mapa
from llm_tb4.coordenadas import ler_coordenadas, ler_direcao
from llm_tb4.interpretador import carregar_destinos, interpretar, resumo

AQUI = Path(__file__).resolve().parent
DESTINOS = carregar_destinos()
MAPAS = AQUI.parents[3] / 'mapas' / 'mapa_lab_novo.yaml'
# Falha conhecida: vírgula decimal com ", " entre parênteses não é lida (recusa, não erra).
NAO_LIDO = 'vá para (1,5, 2,5)'


def casos():
    for arquivo in ('casos_coord.json', 'reserva_coord.json'):
        for frase, esperado in json.loads((AQUI / arquivo).read_text(encoding='utf-8')):
            yield frase, None if frase == NAO_LIDO else esperado


@pytest.mark.parametrize('frase, esperado', list(casos()))
def test_leitura_de_coordenadas(frase, esperado):
    lido = ler_coordenadas(frase)
    assert (list(lido) if lido else None) == esperado


@pytest.mark.parametrize('frase, graus', [
    ('virado para o norte', 0), ('olhando para o oeste', 90), ('sentido sul', 180),
    ('face leste', 270), ('sem direção', None), ('norte ou sul', None)])
def test_direcao_segue_a_convencao_do_turtlebot4(frase, graus):
    assert ler_direcao(frase) == graus


def modelo(acao):
    return lambda frase, destinos: {'acao': acao, 'local': 'nenhum'}


def test_numeros_vem_do_pedido_e_nao_do_modelo():
    def falso(frase, destinos):
        return {'acao': 'ir_para_coordenadas', 'local': 'nenhum', 'x': 99, 'y': 99}
    decisao = interpretar('vá para x -1 y 0', DESTINOS, 1.0, falso, lambda x, y: None)
    assert decisao['acao']['argumentos'] == {'x': -1.0, 'y': 0.0, 'graus': None}


def test_sem_mapa_a_coordenada_e_recusada():
    decisao = interpretar('vá para x -1 y 0', DESTINOS, 1.0, modelo('ir_para_coordenadas'))
    assert resumo(decisao) == 'recusar' and 'mapa' in decisao['motivo']


@pytest.mark.parametrize('xy, serve', [
    ((-0.586, -0.807), True), ((-3.550, -3.063), True), ((-5.608, -0.823), True),
    ((-1.967, 1.030), True), ((100.0, 100.0), False), ((-100.0, 0.0), False)])
def test_mapa_real_aceita_os_pontos_da_patrulha_e_recusa_fora(xy, serve):
    assert (mapa.verificador(MAPAS)(*xy) is None) is serve


def test_mapa_inexistente_recusa_tudo():
    assert 'indisponível' in mapa.verificador('/nao/existe.yaml')(0, 0)


@pytest.mark.parametrize('frase, esperado', [
    ('undock', 'sair_da_base'), ('Faça o undock', 'sair_da_base'), ('desencaixar', 'sair_da_base'),
    ('dock', 'encaixar'), ('encaixe na doca', 'encaixar')])
def test_dock_e_undock_nao_dependem_do_modelo(frase, esperado):
    def proibido(f, d):
        pytest.fail('o modelo não devia ser consultado')
    assert resumo(interpretar(frase, DESTINOS, 1.0, proibido)) == esperado


@pytest.mark.parametrize('acao, bateria, permitido', [
    ('sair_da_base', 0.1, False), ('sair_da_base', 0.5, True), ('encaixar', 0.05, True),
    ('voltar_para_base', None, True)])
def test_bateria_so_barra_quem_sai_da_doca(acao, bateria, permitido):
    decisao = interpretar('faça isso', DESTINOS, bateria, modelo(acao))
    assert decisao['permitido'] is permitido

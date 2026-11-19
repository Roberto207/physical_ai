"""Testes L0 dos cenários do L1 (config/cenarios_l1.yaml) e do conferidor. Sem ROS."""
import json
from pathlib import Path

import pytest

from lab_tb4 import conferir_l1
from lab_tb4.cenarios import CAMPOS, CenarioInvalido, argumentos_launch, carregar

ARQUIVO = Path(__file__).resolve().parents[1] / 'config' / 'cenarios_l1.yaml'
NOMES = ['ciclo', 'l1b', 'dock_falha', 'queda_bateria', 'sem_bateria', 'fora_da_doca',
         'sem_servidor', 'sem_relogio', 'bateria_perdida', 'falhas_seguidas', 'sigint']

# O "case" do infra/docker/teste_l1.sh na tag jazzy-final, transcrito (SIM-04b). A única
# diferença aceita é o nav2_extra do l1b (desvio registrado no YAML e no doc da F3).
BASE = {'battery_start': 0.90, 'drain_per_s': 0.002, 'charge_per_s': 0.05}
ESPERADO = {
    'ciclo': {},
    'l1b': {'nav2_extra': 'nav2_perfil:=turtlebot4'},
    'dock_falha': {'base': {'battery_start': 0.90, 'drain_per_s': 0.004, 'charge_per_s': 0.05,
                            'falhar_dock_n': 1}},
    'queda_bateria': {'base': {'battery_start': 0.99, 'drain_per_s': 0.001,
                               'charge_per_s': 0.05, 'queda_bateria_em_s': 12.0,
                               'queda_bateria_para': 0.30}},
    'sem_bateria': {'base': {**BASE, 'simular_bateria': False}, 'limite_s': 120},
    'fora_da_doca': {'base': {'battery_start': 0.99, 'comecar_na_doca': False},
                     'limite_s': 120},
    'sem_servidor': {'base': {**BASE, 'simular_doca': False}, 'limite_s': 120},
    'sem_relogio': {'subir_nav2': False, 'subir_base': False,
                    'patrulha_extra': 'use_sim_time:=true', 'limite_s': 60},
    'bateria_perdida': {'base': {'battery_start': 0.99, 'drain_per_s': 0.0005,
                                 'charge_per_s': 0.05, 'parar_bateria_em_s': 12.0},
                        'limite_s': 400},
    'falhas_seguidas': {'config': 'teste_tempo_curto.yaml',
                        'base': {'battery_start': 0.99, 'drain_per_s': 0.0005},
                        'limite_s': 400},
    'sigint': {'base': {'battery_start': 0.99, 'drain_per_s': 0.0005}},
}
PADRAO = {'config': 'leve_reduzido.yaml', 'base': BASE, 'limite_s': 900, 'subir_nav2': True,
          'subir_base': True, 'nav2_extra': '', 'patrulha_extra': '', 'sinal_no_fim': True}


@pytest.mark.req('SIM-04')
def test_os_11_cenarios_existem():
    assert list(carregar(ARQUIVO)) == NOMES


@pytest.mark.req('SIM-04b')
@pytest.mark.parametrize('nome', NOMES)
def test_valores_iguais_ao_case_antigo(nome):
    cenario = carregar(ARQUIVO)[nome]
    assert set(cenario) == set(CAMPOS)
    assert cenario == {**PADRAO, **ESPERADO[nome]}


@pytest.mark.req('SIM-04b')
def test_campo_desconhecido_reprova(tmp_path):
    arquivo = tmp_path / 'c.yaml'
    arquivo.write_text(ARQUIVO.read_text() + '\n  extra: {limte_s: 3}\n')
    with pytest.raises(CenarioInvalido):
        carregar(arquivo)


def test_argumentos_launch():
    assert argumentos_launch('a:=1 b:=x') == [('a', '1'), ('b', 'x')]
    assert argumentos_launch('') == []
    with pytest.raises(CenarioInvalido):
        argumentos_launch('sem_valor')


def test_conferir_l1_conhece_os_mesmos_cenarios():
    assert sorted(conferir_l1.CENARIOS) == sorted(NOMES)


def test_conferir_l1_pronto_sem_log_ainda_nao(tmp_path):
    assert conferir_l1.main(['ciclo', str(tmp_path / 'nao_existe.jsonl'), '--pronto']) == 1


def test_conferir_l1_pronto_com_resumo(tmp_path):
    log = tmp_path / 'p.jsonl'
    log.write_text(json.dumps({'evento': 'resumo', 'codigo_saida': 0}) + '\n')
    assert conferir_l1.main(['sigint', str(log), '--pronto']) == 0

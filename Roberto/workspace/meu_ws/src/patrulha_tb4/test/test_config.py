"""Testes da configuração (L0): o que vem do YAML e o que reprova o arquivo."""
import math

import pytest
import yaml
from conftest import dados_config, fazer_config

from patrulha_tb4.config import (ConfigInvalida, Deltas, Limites, calcular_limites, carregar,
                                 limites_validos)


def gravar(pasta, dados):
    caminho = pasta / 'patrulha.yaml'
    caminho.write_text(yaml.safe_dump({'patrulha': dados}))
    return caminho


@pytest.mark.req('PAT-01')
def test_tudo_vem_do_arquivo(tmp_path):
    dados = dados_config(
        bateria={'modo': 'absoluto', 'alta': 0.9, 'baixa': 0.3, 'critica': 0.15},
        tempos={'espera_bateria_s': 11, 'destino_s': 77, 'bateria_perdida_s': 13},
        limites={'falhas_seguidas': 5, 'tentativas_dock': 2})
    cfg = carregar(gravar(tmp_path, dados))
    assert [(p.x, p.y, p.yaw_graus) for p in cfg.pontos] == [(1.0, 0.5, 0), (1.0, 1.5, 90),
                                                              (0.5, 1.5, 180)]
    assert (cfg.pose_inicial.x, cfg.aproximacao_doca.y) == (0.0, 0.5)
    assert cfg.limites == Limites(alta=0.9, baixa=0.3, critica=0.15)
    assert (cfg.tempos.espera_bateria_s, cfg.tempos.destino_s) == (11, 77)
    assert cfg.tempos.bateria_perdida_s == 13
    assert (cfg.falhas_seguidas, cfg.tentativas_dock) == (5, 2)
    assert cfg.mapa == str(tmp_path / 'mapa.yaml')  # relativo à pasta da configuração
    assert len(cfg.hash_config) == 64


@pytest.mark.req('PAT-01')
def test_padroes_sao_os_do_define(cfg):
    assert cfg.modo_bateria == 'absoluto'
    assert cfg.limites == Limites(alta=0.95, baixa=0.20, critica=0.10)
    t = cfg.tempos
    assert (t.espera_bateria_s, t.confirma_dock_s, t.cancelar_s, t.destino_s, t.servidor_s,
            t.encerrar_s, t.sem_relogio_s) == (30, 5, 2, 120, 30, 3, 10)
    assert (cfg.falhas_seguidas, cfg.tentativas_dock, cfg.margem_obstaculo_m) == (3, 3, 0.25)


@pytest.mark.req('PAT-18')
def test_bateria_perdida_tem_padrao_por_ambiente():
    assert fazer_config(ambiente='leve').tempos.bateria_perdida_s == 10
    assert fazer_config(ambiente='gazebo').tempos.bateria_perdida_s == 30
    with pytest.raises(ConfigInvalida):  # no real, o valor vem da medição no laboratório
        fazer_config(ambiente='real')
    assert fazer_config(ambiente='real',
                        tempos={'bateria_perdida_s': 6}).tempos.bateria_perdida_s == 6


def test_tempo_simulado_segue_o_ambiente():
    assert fazer_config(ambiente='leve').usa_tempo_simulado
    assert fazer_config(ambiente='gazebo').usa_tempo_simulado
    assert not fazer_config(ambiente='real',
                            tempos={'bateria_perdida_s': 6}).usa_tempo_simulado


@pytest.mark.req('VAL-04')
def test_modo_de_bateria_desconhecido_e_reprovado():
    with pytest.raises(ConfigInvalida) as erro:
        fazer_config(bateria={'modo': 'automatico'})
    assert erro.value.motivo == 'modo_invalido'


@pytest.mark.req('VAL-04')
@pytest.mark.parametrize('bateria', [
    {'alta': 0.95, 'baixa': 0.20, 'critica': 0.20},   # crítica igual à baixa
    {'alta': 0.15, 'baixa': 0.20, 'critica': 0.10},   # alta abaixo da baixa
    {'alta': 1.01, 'baixa': 0.20, 'critica': 0.10},   # acima de 1
    {'alta': 0.95, 'baixa': 0.20, 'critica': 0.0},    # crítica zero
    {'alta': 0.95, 'baixa': 0.20, 'critica': -0.1},
    {'alta': math.nan, 'baixa': 0.20, 'critica': 0.10},
    {'alta': math.inf, 'baixa': 0.20, 'critica': 0.10},
    {'alta': 'muito', 'baixa': 0.20, 'critica': 0.10},
])
def test_limites_absolutos_fora_de_ordem_sao_reprovados(bateria):
    with pytest.raises(ConfigInvalida) as erro:
        fazer_config(bateria=bateria)
    assert erro.value.motivo == 'limites_invalidos'


@pytest.mark.req('VAL-04')
def test_alta_igual_a_1_e_aceita():
    assert fazer_config(bateria={'alta': 1.0}).limites.alta == 1.0


@pytest.mark.req('VAL-04')
@pytest.mark.parametrize('deltas', [
    {'delta_alta': 0.01, 'delta_baixa': 0.01, 'delta_critica': 0.02},
    {'delta_alta': -0.001, 'delta_baixa': 0.01, 'delta_critica': 0.02},
    {'delta_alta': 0.005, 'delta_baixa': 0.03, 'delta_critica': 0.02},
    {'delta_alta': 0.005, 'delta_baixa': 0.01, 'delta_critica': math.nan},
])
def test_deltas_fora_de_ordem_sao_reprovados_no_modo_relativo(deltas):
    with pytest.raises(ConfigInvalida) as erro:
        fazer_config(bateria={'modo': 'relativo', **deltas})
    assert erro.value.motivo == 'limites_invalidos'


@pytest.mark.req('PAT-21')
def test_modo_relativo_ignora_os_limites_absolutos_e_calcula_de_b0():
    cfg = fazer_config(bateria={'modo': 'relativo', 'alta': 0.1, 'baixa': 0.9, 'critica': 5})
    assert cfg.limites is None  # só existem depois da primeira bateria
    assert cfg.deltas == Deltas(alta=0.005, baixa=0.01, critica=0.02)
    limites = calcular_limites(cfg.deltas, 0.87)
    assert (limites.alta, limites.baixa, limites.critica) == pytest.approx((0.865, 0.86, 0.85))
    assert limites_validos(limites)


@pytest.mark.req('VAL-04')
def test_limites_calculados_de_b0_ruim_nao_sao_validos():
    deltas = Deltas(alta=0.005, baixa=0.01, critica=0.02)
    assert not limites_validos(calcular_limites(deltas, math.nan))
    assert not limites_validos(calcular_limites(deltas, 0.02))   # crítica daria zero
    assert not limites_validos(calcular_limites(deltas, 1.2))    # alta passaria de 1


@pytest.mark.req('VAL-01')
@pytest.mark.parametrize('campo', ['ambiente', 'mapa', 'pose_inicial', 'aproximacao_doca',
                                   'pontos'])
def test_campo_obrigatorio_faltando_e_reprovado(campo):
    with pytest.raises(ConfigInvalida) as erro:
        fazer_config(**{campo: None})
    assert campo in str(erro.value)


@pytest.mark.req('VAL-01')
def test_configuracoes_malformadas_sao_reprovadas(tmp_path):
    with pytest.raises(ConfigInvalida):
        fazer_config(ambiente='marte')
    with pytest.raises(ConfigInvalida):
        fazer_config(pontos=[])
    with pytest.raises(ConfigInvalida):
        fazer_config(pontos=[{'x': 1.0, 'y': 'dois', 'yaw_graus': 0}])
    with pytest.raises(ConfigInvalida):
        fazer_config(tempos={'destino_s': 0})
    with pytest.raises(ConfigInvalida):
        fazer_config(limites={'tentativas_dock': 0})
    with pytest.raises(ConfigInvalida) as erro:
        carregar(tmp_path / 'nao-existe.yaml')
    assert erro.value.motivo == 'arquivo_ilegivel'
    ruim = tmp_path / 'ruim.yaml'
    ruim.write_text('patrulha: [1, 2')
    with pytest.raises(ConfigInvalida) as erro:
        carregar(ruim)
    assert erro.value.motivo == 'yaml_invalido'


def test_perfil_inf_devagar_limita_a_velocidade_a_0_15():
    """INF-02: no perfil do laboratório, o velocity_smoother não passa de 0,15 m/s em x."""
    from pathlib import Path
    perfil = Path(__file__).resolve().parents[1] / 'config' / 'nav2_inf_devagar.yaml'
    smoother = yaml.safe_load(perfil.read_text())['velocity_smoother']['ros__parameters']
    assert smoother['max_velocity'][0] <= 0.15
    assert smoother['min_velocity'][0] >= -0.15


@pytest.mark.req('PAT-01')
@pytest.mark.parametrize('arquivo', ['leve_reduzido.yaml', 'teste_tempo_curto.yaml',
                                     'gazebo_maze.yaml', 'warehouse_original.yaml'])
def test_as_configuracoes_do_pacote_carregam(arquivo):
    from pathlib import Path
    cfg = carregar(Path(__file__).resolve().parents[1] / 'config' / arquivo)
    assert len(cfg.pontos) >= 3
    assert cfg.usa_tempo_simulado

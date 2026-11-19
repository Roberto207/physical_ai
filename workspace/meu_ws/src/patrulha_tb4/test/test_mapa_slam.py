"""Testes do conferir_mapa (L0), com mapas de mentira do conftest."""
import pytest
from conftest import escrever_mapa

from patrulha_tb4 import mapa_slam, pontos

# 4 x 2 células de 0,5 m: metade livre, 2 paredes, 2 não mapeadas.
SALA = [
    '#..?',
    '#..?',
]


def test_resumo_conta_as_celulas_e_o_tamanho(tmp_path):
    resumo = mapa_slam.resumir(pontos.ler_mapa(escrever_mapa(tmp_path, SALA)))
    assert (resumo.largura_m, resumo.altura_m) == (2.0, 1.0)
    assert resumo.fracao_livre == pytest.approx(0.5)
    assert resumo.fracao_ocupada == pytest.approx(0.25)
    assert resumo.fracao_desconhecida == pytest.approx(0.25)
    assert resumo.estado_origem == pontos.OCUPADA   # (0, 0) cai na parede da esquerda
    assert resumo.utilizavel


def test_origem_deslocada_como_num_mapa_de_slam(tmp_path):
    # O SLAM põe a origem do mapa no canto, e (0, 0) é onde o robô começou.
    caminho = escrever_mapa(tmp_path, SALA, origem=(-0.75, -0.5, 0.0))
    assert mapa_slam.resumir(pontos.ler_mapa(caminho)).estado_origem == pontos.LIVRE


def test_origem_fora_do_mapa_so_avisa(tmp_path, capsys):
    caminho = escrever_mapa(tmp_path, SALA, origem=(5.0, 5.0, 0.0))
    assert mapa_slam.main([str(caminho)]) == 0
    assert 'origem está fora do mapa' in capsys.readouterr().out


def test_mapa_sem_celula_livre_e_recusado(tmp_path, capsys):
    caminho = escrever_mapa(tmp_path, ['??', '??'])
    assert mapa_slam.main([str(caminho)]) == 2
    assert 'nenhuma célula livre' in capsys.readouterr().out


def test_pouca_area_livre_so_avisa(tmp_path, capsys):
    linhas = ['?' * 30] * 3 + ['.' + '?' * 29]   # 1 célula livre em 120
    assert mapa_slam.main([str(escrever_mapa(tmp_path, linhas))]) == 0
    assert 'pouca área livre' in capsys.readouterr().out


def test_mapa_ilegivel_e_recusado(tmp_path, capsys):
    (tmp_path / 'quebrado.yaml').write_text('image: nao_existe.pgm\nresolution: 0.05\n'
                                            'origin: [0, 0, 0]\n')
    assert mapa_slam.main([str(tmp_path / 'quebrado.yaml')]) == 2
    assert 'RECUSADO' in capsys.readouterr().out

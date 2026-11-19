"""Testes da validação das poses contra o mapa (L0), com mapas de mentira."""
import pytest
import yaml
from conftest import dados_config, escrever_mapa

from patrulha_tb4 import pontos
from patrulha_tb4.config import ConfigInvalida, carregar

# Mapa de 6 x 5 células de 0,5 m (3,0 m x 2,5 m), com a origem em (0, 0).
# A primeira linha do texto é o topo (y entre 2,0 e 2,5).
SALA = [
    '######',
    '#....#',
    '#....?',
    '#....#',
    '######',
]


def config_com(pasta, mapa_yaml, **mudancas):
    dados = dados_config(mapa=str(mapa_yaml), **mudancas)
    caminho = pasta / 'patrulha.yaml'
    caminho.write_text(yaml.safe_dump({'patrulha': dados}))
    return caminho


@pytest.fixture
def sala(tmp_path):
    return pontos.ler_mapa(escrever_mapa(tmp_path, SALA))


def test_conversao_de_metros_para_celula(sala):
    assert sala.celula(0.0, 0.0) == (0, 0)
    assert sala.celula(0.75, 1.25) == (1, 2)
    assert sala.celula(2.99, 2.49) == (5, 4)
    assert sala.celula(3.0, 1.0) is None and sala.celula(-0.01, 1.0) is None
    assert sala.estado(0, 0) == pontos.OCUPADA      # canto de baixo, à esquerda
    assert sala.estado(1, 1) == pontos.LIVRE
    assert sala.estado(5, 2) == pontos.DESCONHECIDA


def test_origem_deslocada_como_num_mapa_de_slam(tmp_path):
    mapa = pontos.ler_mapa(escrever_mapa(tmp_path, SALA, origem=(-1.5, -1.0, 0.0)))
    assert mapa.celula(-1.5, -1.0) == (0, 0)
    assert mapa.celula(0.0, 0.0) == (3, 2)
    assert mapa.celula(1.6, 0.0) is None


@pytest.mark.req('VAL-02')
@pytest.mark.parametrize('x, y, margem, esperado', [
    (5.0, 1.0, 0.25, pontos.FORA_DO_MAPA),
    (0.25, 1.25, 0.25, pontos.CELULA_OCUPADA),
    (2.75, 1.25, 0.25, pontos.CELULA_DESCONHECIDA),
    (0.75, 1.25, 0.60, pontos.PERTO_DE_OBSTACULO),  # parede na célula vizinha (0,5 m)
    (0.75, 1.25, 0.25, None),                       # mesma pose, com a margem padrão
    (1.75, 1.25, 0.60, None),                       # meio da sala
])
def test_motivos_que_reprovam_uma_pose(sala, x, y, margem, esperado):
    assert pontos.motivo_da_pose(sala, x, y, margem) == esperado


@pytest.mark.req('VAL-01')
def test_configuracao_boa_passa_e_confere_todas_as_poses(tmp_path):
    mapa_yaml = escrever_mapa(tmp_path, SALA)
    cfg, problemas = pontos.validar_configuracao(config_com(
        tmp_path, mapa_yaml,
        pose_inicial={'x': 0.75, 'y': 0.75, 'yaw_graus': 0},
        aproximacao_doca={'x': 1.25, 'y': 0.75, 'yaw_graus': 0},
        pontos=[{'x': 1.75, 'y': 1.25, 'yaw_graus': 0}, {'x': 2.25, 'y': 1.75, 'yaw_graus': 90}]))
    assert problemas == []
    assert [p.nome for p in cfg.poses_nomeadas()] == ['pose_inicial', 'aproximacao_doca',
                                                      'pontos[0]', 'pontos[1]']


@pytest.mark.req('VAL-01')
@pytest.mark.req('VAL-02')
def test_cada_pose_ruim_aparece_com_o_nome_e_o_motivo(tmp_path):
    mapa_yaml = escrever_mapa(tmp_path, SALA)
    _, problemas = pontos.validar_configuracao(config_com(
        tmp_path, mapa_yaml,
        pose_inicial={'x': 0.75, 'y': 0.75, 'yaw_graus': 0},
        aproximacao_doca={'x': 0.25, 'y': 0.25, 'yaw_graus': 0},   # dentro da parede
        pontos=[{'x': 1.75, 'y': 1.25, 'yaw_graus': 0},
                {'x': 9.0, 'y': 9.0, 'yaw_graus': 0},               # erro de digitação
                {'x': 2.75, 'y': 1.25, 'yaw_graus': 0}]))           # área não mapeada
    assert problemas == [('aproximacao_doca', pontos.CELULA_OCUPADA),
                         ('pontos[1]', pontos.FORA_DO_MAPA),
                         ('pontos[2]', pontos.CELULA_DESCONHECIDA)]


@pytest.mark.req('VAL-01')
def test_mapa_que_nao_abre_reprova_a_configuracao(tmp_path):
    with pytest.raises(ConfigInvalida) as erro:
        pontos.validar_configuracao(config_com(tmp_path, tmp_path / 'sumiu.yaml'))
    assert erro.value.motivo == 'mapa_invalido'


@pytest.mark.req('VAL-03')
def test_comando_validar_pontos_roda_sem_ros(tmp_path, capsys):
    mapa_yaml = escrever_mapa(tmp_path, SALA)
    boa = config_com(tmp_path, mapa_yaml,
                     pose_inicial={'x': 0.75, 'y': 0.75, 'yaw_graus': 0},
                     aproximacao_doca={'x': 1.25, 'y': 0.75, 'yaw_graus': 0},
                     pontos=[{'x': 1.75, 'y': 1.25, 'yaw_graus': 0}])
    assert pontos.main([str(boa)]) == 0
    assert 'APROVADA' in capsys.readouterr().out
    assert carregar(boa).mapa == str(mapa_yaml)

    ruim = config_com(tmp_path, mapa_yaml,
                      pose_inicial={'x': 0.75, 'y': 0.75, 'yaw_graus': 0},
                      aproximacao_doca={'x': 1.25, 'y': 0.75, 'yaw_graus': 0},
                      pontos=[{'x': 0.25, 'y': 1.25, 'yaw_graus': 0}])
    assert pontos.main([str(ruim)]) == 2
    saida = capsys.readouterr().out
    assert 'pontos[0]' in saida and pontos.CELULA_OCUPADA in saida and 'REPROVADA' in saida


@pytest.mark.req('VAL-03')
def test_o_modulo_de_validacao_nao_importa_ros():
    import sys
    assert 'rclpy' not in sys.modules


def test_pgm_em_texto_e_com_comentarios(tmp_path):
    (tmp_path / 'm.pgm').write_bytes(
        b'P2\n# feito a mao\n3 2\n# outro\n255\n0 254 254\n254 205 0\n')
    largura, altura, maximo, pixels = pontos.ler_pgm(tmp_path / 'm.pgm')
    assert (largura, altura, maximo) == (3, 2, 255)
    assert pixels == bytes([0, 254, 254, 254, 205, 0])


def test_mapas_quebrados_dao_erro_claro(tmp_path):
    (tmp_path / 'curto.pgm').write_bytes(b'P5\n4 4\n255\n\x00\x00')
    with pytest.raises(pontos.MapaInvalido):
        pontos.ler_pgm(tmp_path / 'curto.pgm')
    (tmp_path / 'm.yaml').write_text('image: m.png\nresolution: 0.05\norigin: [0, 0, 0]\n')
    with pytest.raises(pontos.MapaInvalido):
        pontos.ler_mapa(tmp_path / 'm.yaml')
    (tmp_path / 'sem.yaml').write_text('image: m.pgm\n')
    with pytest.raises(pontos.MapaInvalido):
        pontos.ler_mapa(tmp_path / 'sem.yaml')

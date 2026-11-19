"""Testes do log JSONL (L0): lista fechada, campos obrigatórios, início e resumo."""
import json
import re
from pathlib import Path

import pytest
from conftest import Mundo

from patrulha_tb4 import decisao as d
from patrulha_tb4.registro import ESTADOS, EVENTOS, Registro, hash_codigo

RAIZ = Path(__file__).resolve().parents[1]
INICIO = dict(hash_codigo='a' * 64, hash_config='b' * 64, versao='0.1.0', ambiente='leve',
              modelo='standard')


def linhas(caminho):
    return [json.loads(linha) for linha in Path(caminho).read_text().splitlines()]


@pytest.fixture
def registro(tmp_path):
    relogio = iter(range(5000, 6000))
    reg = Registro(tmp_path / 'log' / 'patrulha.jsonl', relogio_parede=lambda: next(relogio))
    yield reg
    reg.fechar()


@pytest.mark.req('OBS-01')
def test_cada_linha_tem_os_campos_obrigatorios(registro):
    registro.gravar('inicio', 'iniciando', None, 0.0, **INICIO)
    registro.gravar('destino_ok', 'patrulhando', 0.42, 12.5, ponto=1, resultado=4)
    primeira, segunda = linhas(registro.caminho)
    for linha in (primeira, segunda):
        assert {'t', 't_parede', 'evento', 'estado', 'bateria'} <= set(linha)
    assert primeira['bateria'] is None  # ainda não chegou
    assert segunda == {'t': 12.5, 't_parede': segunda['t_parede'], 'evento': 'destino_ok',
                       'estado': 'patrulhando', 'bateria': 0.42, 'ponto': 1, 'resultado': 4}
    assert segunda['t_parede'] > primeira['t_parede']


@pytest.mark.req('OBS-01')
def test_evento_estado_ou_campo_fora_do_esquema_e_recusado(registro):
    registro.gravar('inicio', 'iniciando', None, 0.0, **INICIO)
    with pytest.raises(ValueError):
        registro.gravar('robo_feliz', 'patrulhando', 0.5, 1.0)
    with pytest.raises(ValueError):
        registro.gravar('destino_ok', 'passeando', 0.5, 1.0)
    with pytest.raises(ValueError):
        registro.gravar('destino_ok', 'patrulhando', 0.5, 1.0, velocidade=3)
    with pytest.raises(ValueError):
        registro.gravar('destino_ok', 'patrulhando', 0.5, 1.0, b0=0.5)  # só em limites_bateria
    assert len(linhas(registro.caminho)) == 1


@pytest.mark.req('OBS-01')
def test_a_lista_de_eventos_e_a_do_design():
    design = RAIZ.parents[3] / 'specs' / 'patrol-inf' / 'DESIGN.md'
    if not design.exists():
        pytest.skip('DESIGN.md fora de alcance (dentro do container)')
    texto = design.read_text()
    trecho = texto.split('Lista fechada de eventos:')[1].split('Os códigos de saída')[0]
    assert tuple(re.findall(r'^- `(\w+)`$', trecho, flags=re.M)) == EVENTOS
    estados = re.search(r'\| `estado` \| Sim \| (.+) \|', texto).group(1)
    assert tuple(re.findall(r'`(\w+)`', estados)) == ESTADOS


@pytest.mark.req('OBS-01')
def test_todo_evento_que_a_decisao_gera_esta_na_lista(cfg):
    cenarios = [
        Mundo(cfg, bateria=0.99, descarga=0.005, duracao_destino=30).rodar(400),
        Mundo(cfg, bateria=0.99, descarga=0.0001, pontos_inalcancaveis={0, 1, 2}).rodar(200),
        Mundo(cfg, bateria=0.99, descarga=0.02, dock_sem_confirmar=99).rodar(300),
        Mundo(cfg, bateria=0.99, descarga=0.0001, parar_bateria_em=20).rodar(200),
        Mundo(cfg, publica_bateria=False).rodar(60),
        Mundo(cfg, na_base=False, bateria=0.99).rodar(10),
        Mundo(cfg, servidores_ok=False).rodar(60),
        Mundo(cfg, bateria=0.99, falhar_undock=True).rodar(30),
        Mundo(cfg, usa_sim_time=True, relogio_ate=0).rodar(30),
        Mundo(cfg, bateria=0.99, descarga=0.0001, pedido_doca_em=40).rodar(400),
    ]
    vistos = set()
    for mundo in cenarios:
        for evento in mundo.eventos:
            assert evento['evento'] in EVENTOS and evento['estado'] in ESTADOS
            vistos.add(evento['evento'])
    # inicio e resumo são do nó; config_invalida e limites_bateria têm teste próprio.
    assert set(EVENTOS) - vistos <= {'inicio', 'resumo', 'config_invalida', 'limites_bateria',
                                     'encerrado', 'bateria_critica'}


@pytest.mark.req('OBS-03')
def test_inicio_e_o_primeiro_evento_e_traz_a_identidade(registro, tmp_path):
    with pytest.raises(ValueError):
        registro.gravar('destino_ok', 'patrulhando', 0.5, 1.0)  # antes do inicio: recusado
    with pytest.raises(ValueError):
        registro.gravar('inicio', 'iniciando', None, 0.0, versao='0.1.0')  # faltam campos
    registro.gravar('inicio', 'iniciando', None, 0.0, **INICIO)
    primeira = linhas(registro.caminho)[0]
    assert primeira['evento'] == 'inicio'
    for campo, valor in INICIO.items():
        assert primeira[campo] == valor


@pytest.mark.req('OBS-03')
def test_hash_do_codigo_cobre_os_py_e_o_launch_e_ignora_a_config(tmp_path):
    pacote, launch, config = tmp_path / 'pacote', tmp_path / 'launch', tmp_path / 'config'
    for pasta in (pacote, launch, config):
        pasta.mkdir()
    (pacote / 'a.py').write_text('x = 1\n')
    (launch / 'p.launch.py').write_text('y = 2\n')
    (config / 'c.yaml').write_text('z: 3\n')
    pastas = [('patrulha_tb4', pacote), ('launch', launch)]
    original = hash_codigo(pastas)
    assert len(original) == 64

    (config / 'c.yaml').write_text('z: 4\n')
    (pacote / '__pycache__').mkdir()
    (pacote / '__pycache__' / 'a.cpython-312.pyc').write_bytes(b'lixo')
    assert hash_codigo(pastas) == original          # config e cache não contam

    (launch / 'p.launch.py').write_text('y = 3\n')
    com_launch = hash_codigo(pastas)
    assert com_launch != original                   # o launch conta
    (pacote / 'a.py').write_text('x = 2\n')
    assert hash_codigo(pastas) != com_launch        # o código conta

    # O mesmo conteúdo em outra pasta (fonte ou instalado) dá o mesmo hash.
    copia = tmp_path / 'outro'
    copia.mkdir()
    (copia / 'a.py').write_text('x = 2\n')
    assert hash_codigo([('patrulha_tb4', copia), ('launch', launch)]) == hash_codigo(pastas)


@pytest.mark.req('OBS-03')
def test_hash_do_pacote_de_verdade_e_estavel():
    pastas = [('patrulha_tb4', RAIZ / 'patrulha_tb4'), ('launch', RAIZ / 'launch')]
    assert hash_codigo(pastas) == hash_codigo(pastas)


@pytest.mark.req('OBS-02')
def test_resumo_tem_os_numeros_da_execucao(registro):
    registro.gravar('inicio', 'iniciando', None, 0.0, **INICIO)
    registro.gravar('destino_falhou', 'patrulhando', 0.80, 10.0, ponto=0, resultado=6)
    registro.gravar('dock_nao_confirmado', 'indo_doca', 0.18, 50.0, detalhe='sem_is_docked')
    registro.gravar('dock_ok', 'carregando', 0.12, 60.0)
    registro.observar_bateria(0.07)
    registro.gravar_resumo('encerrando', 0.5, 90.0, voltas=2, codigo_saida=0)
    registro.gravar_resumo('encerrando', 0.5, 91.0, voltas=2, codigo_saida=0)  # não duplica
    todas = linhas(registro.caminho)
    resumo = todas[-1]
    assert [linha['evento'] for linha in todas].count('resumo') == 1
    assert resumo['voltas'] == 2
    assert resumo['destinos_falhos'] == 1
    assert resumo['docks_confirmados'] == 1
    assert resumo['tentativas_dock'] == 2
    assert resumo['bateria_minima'] == 0.07
    assert resumo['duracao_s'] > 0
    assert resumo['codigo_saida'] == 0


@pytest.mark.req('OBS-02')
@pytest.mark.parametrize('codigo', [0, 2, 3, 4, 5, 6, 7, 8, 9])
def test_resumo_e_gravado_em_qualquer_codigo_de_saida(tmp_path, codigo):
    registro = Registro(tmp_path / f'{codigo}.jsonl')
    registro.gravar('inicio', 'iniciando', None, 0.0, **INICIO)
    registro.gravar_resumo('encerrando', None, 1.0, voltas=0, codigo_saida=codigo)
    registro.fechar()
    resumo = linhas(registro.caminho)[-1]
    assert resumo['evento'] == 'resumo' and resumo['codigo_saida'] == codigo
    assert resumo['bateria_minima'] is None  # nunca chegou: fica null, mas o campo existe


@pytest.mark.req('OBS-02')
def test_codigos_de_saida_sao_os_do_define():
    assert (d.CODIGO_ENCERRADO, d.CODIGO_CONFIG, d.CODIGO_SEM_BATERIA, d.CODIGO_DOCK,
            d.CODIGO_UNDOCK, d.CODIGO_FORA_DA_DOCA, d.CODIGO_FALHAS, d.CODIGO_SERVIDOR,
            d.CODIGO_SEM_RELOGIO) == (0, 2, 3, 4, 5, 6, 7, 8, 9)

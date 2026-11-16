"""TST-02: a checagem de rastreio roda junto com a suíte e sabe falhar."""
import checar_rastreio
import pytest


def test_todo_requisito_l0_tem_teste():
    if not checar_rastreio.DESIGN_PADRAO.exists():
        pytest.skip('DESIGN.md fora de alcance (dentro do container)')
    exigidos, sem_teste = checar_rastreio.faltando()
    assert len(exigidos) >= 30
    assert sem_teste == []


def test_expande_faixas_e_listas():
    assert checar_rastreio.ids_da_celula('PAT-09 a PAT-11') == ['PAT-09', 'PAT-10', 'PAT-11']
    assert checar_rastreio.ids_da_celula('PAT-21, PAT-21b') == ['PAT-21', 'PAT-21b']
    assert checar_rastreio.ids_da_celula('PAT-01, TST-07') == ['PAT-01', 'TST-07']


def test_so_conta_pat_val_e_obs_com_sim_na_coluna_l0():
    design = ('### Requisito → teste\n\n'
              '| Requisitos | L0 (pytest) | L1 |\n|---|---|---|\n'
              '| PAT-01, TST-07 | Sim (lint) | |\n'
              '| AMB-01, AMB-02 | | Sim |\n'
              '| OBS-01 a OBS-03 | Sim | Sim |\n'
              '| TST-08 | | |\n')
    assert checar_rastreio.ids_l0(design) == ['PAT-01', 'OBS-01', 'OBS-02', 'OBS-03']


def test_a_checagem_falha_quando_falta_teste(tmp_path):
    design = tmp_path / 'DESIGN.md'
    design.write_text('### Requisito → teste\n\n| Requisitos | L0 |\n|---|---|\n'
                      '| PAT-98, PAT-99 | Sim |\n')
    (tmp_path / 'test_x.py').write_text('@pytest.mark.req("PAT-98")\ndef test_x(): pass\n')
    exigidos, sem_teste = checar_rastreio.faltando(design, tmp_path)
    assert exigidos == ['PAT-98', 'PAT-99'] and sem_teste == ['PAT-99']

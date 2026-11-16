#!/usr/bin/env python3
"""TST-02: todo requisito PAT, VAL e OBS marcado como L0 no DESIGN precisa ter teste.

Lê a tabela "Requisito → teste" do DESIGN.md, pega os IDs com "Sim" na coluna L0 e
procura `@pytest.mark.req("<ID>")` nos arquivos de teste. Sai com código 1 se faltar algum.

    python3 test/checar_rastreio.py [caminho/do/DESIGN.md]
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESIGN_PADRAO = AQUI.parents[4] / 'specs' / 'patrol-inf' / 'DESIGN.md'
GRUPOS = ('PAT', 'VAL', 'OBS')
ID = r'(?:PAT|VAL|OBS|TST|AMB|INF)-\d+[a-z]?'


def ids_da_celula(celula):
    """Expande 'PAT-09 a PAT-11' e 'PAT-21, PAT-21b' em IDs soltos."""
    ids = []
    for trecho in celula.split(','):
        faixa = re.fullmatch(rf'\s*({ID})\s+a\s+({ID})\s*', trecho)
        if faixa:
            (grupo, inicio), (_, fim) = (parte.split('-') for parte in faixa.groups())
            ids += [f'{grupo}-{numero:02d}' for numero in range(int(inicio), int(fim) + 1)]
        else:
            ids += re.findall(ID, trecho)
    return ids


def ids_l0(texto_design):
    """IDs dos grupos PAT, VAL e OBS com "Sim" na coluna L0 da tabela do DESIGN."""
    secao = texto_design.split('### Requisito → teste')[1].split('\n## ')[0]
    exigidos = []
    for linha in secao.splitlines():
        colunas = [coluna.strip() for coluna in linha.strip().strip('|').split('|')]
        if len(colunas) < 2 or not colunas[1].startswith('Sim'):
            continue
        exigidos += [i for i in ids_da_celula(colunas[0]) if i.split('-')[0] in GRUPOS]
    return exigidos


def ids_testados(pasta_de_testes):
    marcados = set()
    for arquivo in Path(pasta_de_testes).glob('test_*.py'):
        marcados |= set(re.findall(r'''@pytest\.mark\.req\(['"]([^'"]+)['"]\)''',
                                   arquivo.read_text()))
    return marcados


def faltando(caminho_design=DESIGN_PADRAO, pasta_de_testes=AQUI):
    exigidos = ids_l0(Path(caminho_design).read_text())
    if not exigidos:
        raise SystemExit('Não achei nenhum ID L0 na tabela do DESIGN: o formato mudou?')
    testados = ids_testados(pasta_de_testes)
    return exigidos, [i for i in exigidos if i not in testados]


def main():
    design = sys.argv[1] if len(sys.argv) > 1 else DESIGN_PADRAO
    exigidos, sem_teste = faltando(design)
    if sem_teste:
        print(f'FALTA teste para {len(sem_teste)} de {len(exigidos)} requisitos L0: '
              + ', '.join(sem_teste))
        return 1
    print(f'OK: os {len(exigidos)} requisitos L0 (PAT, VAL e OBS) têm teste marcado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

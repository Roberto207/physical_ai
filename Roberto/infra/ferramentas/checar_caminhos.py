#!/usr/bin/env python3
"""Confere que os caminhos citados nos documentos vivos existem (P3 da spec enxugamento).

Lê os `.md` do projeto, menos `docs/historico/` e `docs/tarefas/` (históricos não são
atualizados), as specs `enxugamento` e `migracao-humble` (descrevem arquivos que saem ou
mudam de lugar) e `estudo/` (local, fora do git), e extrai os trechos entre crases cujo primeiro segmento é uma pasta de topo do
projeto (`docs/`, `infra/`, `specs/`, `workspace/`). Sai com 1 e lista cada citação cujo
arquivo ou pasta não existe. Python puro, sem dependências: roda no job `lint` do CI.

Uso: python3 infra/ferramentas/checar_caminhos.py
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]  # a pasta Roberto/
PASTAS = ('docs', 'infra', 'specs', 'workspace')
HISTORICO = ('docs/historico', 'docs/tarefas')
# Specs que descrevem a própria mudança de arquivos: citam o que sai e o que muda de lugar.
SPECS_DE_MUDANCA = ('specs/enxugamento', 'specs/migracao-humble')
# Caminhos legítimos que não estão no git: saídas geradas em cada máquina, e arquivos que
# a spec cita como o que ainda será produzido (ex.: o mapa do laboratório, feito no INF).
FORA_DO_GIT = (
    'workspace/logs',
    'workspace/meu_ws/build', 'workspace/meu_ws/install', 'workspace/meu_ws/log',
    'workspace/mapas/lab.',
)
BLOCO = re.compile(r'```.*?```', re.S)
TRECHO = re.compile(r'`([^`\n]+)`')
PLACEHOLDER = re.compile(r'[<>*{}$|\[\]]|\.\.\.|AAAA')


def citacoes(texto):
    """Caminhos candidatos de um texto: tokens dos trechos entre crases fora de blocos."""
    for trecho in TRECHO.findall(BLOCO.sub('', texto)):
        for token in trecho.split():
            token = re.split(r'[#:]', token.strip('.,;:()'), maxsplit=1)[0]
            if token.split('/', 1)[0] in PASTAS and '/' in token and not PLACEHOLDER.search(token):
                yield token


def main():
    erros = []
    for md in sorted(RAIZ.rglob('*.md')):
        rel = md.relative_to(RAIZ).as_posix()
        if rel.startswith(HISTORICO + SPECS_DE_MUDANCA) or rel.startswith('estudo/') or '/build/' in rel:
            continue
        for caminho in dict.fromkeys(citacoes(md.read_text(encoding='utf-8'))):
            if caminho.startswith(FORA_DO_GIT):
                continue
            if not (RAIZ / caminho).exists():
                erros.append(f'{rel}: `{caminho}` não existe')
    for erro in erros:
        print(erro)
    print(f'{len(erros)} citação(ões) quebrada(s)' if erros else 'caminhos ok')
    return 1 if erros else 0


if __name__ == '__main__':
    sys.exit(main())

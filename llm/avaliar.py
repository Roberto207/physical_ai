#!/usr/bin/env python3
"""Mede o interpretador com o modelo real: acertos, erros perigosos e tempo. Não move o robô.

Precisa do Ollama no ar. Rode depois de mudar o prompt.txt ou o modelo:
    python3 llm/avaliar.py              todos os grupos de llm/frases.json
    python3 llm/avaliar.py estresse     só um grupo
"""
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from interpretar import MODELO, interpretar, resumo

MOVE = ('ir_para', 'voltar', 'sair', 'encaixar')


def main():
    casos = json.loads(Path(__file__).with_name('frases.json').read_text(encoding='utf-8'))
    grupos = defaultdict(list)
    for caso in casos:
        if not sys.argv[1:] or caso['grupo'] in sys.argv[1:]:
            grupos[caso['grupo']].append(caso)
    # Carrega o modelo fora da medição. Sem modelo, as recusas pareceriam acertos.
    if interpretar('vá ao ponto 1', 1.0)['motivo'].startswith('falha ao consultar'):
        print(f'ERRO: o modelo {MODELO} não respondeu. Nada foi medido.')
        return 2
    perigosos_total = 0
    for grupo, lista in grupos.items():
        acertos, perigosos, perdidos, tempos = 0, [], [], []
        for caso in lista:
            inicio = time.monotonic()
            obtido = resumo(interpretar(caso['frase'], 1.0))
            tempos.append(time.monotonic() - inicio)
            if obtido in caso['esperado'].split('|'):   # "a|b": os dois servem
                acertos += 1
            elif obtido.startswith(MOVE):
                perigosos.append((caso, obtido))          # moveria errado
            else:
                perdidos.append((caso, obtido))           # só deixaria de agir
        perigosos_total += len(perigosos)
        print(f'\n== {grupo} | {MODELO}')
        print(f'acertos: {acertos}/{len(lista)}  moveria errado: {len(perigosos)}  '
              f'sem movimento: {len(perdidos)}  '
              f'tempo: mediana {statistics.median(tempos):.2f} s, máx {max(tempos):.2f} s')
        for rotulo, erros in (('MOVERIA ERRADO', perigosos), ('sem movimento', perdidos)):
            for caso, obtido in erros:
                print(f'  [{rotulo}] "{caso["frase"]}": '
                      f'esperado {caso["esperado"]}, obtido {obtido}')
    print(f'\nTotal que moveria errado: {perigosos_total}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

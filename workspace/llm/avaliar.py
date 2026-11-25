"""Mede o interpretador com o modelo real: acertos, erros perigosos e tempo de resposta.

Precisa do Ollama rodando. Não move o robô.
Uso: python3 avaliar.py [testes_frases/ajuste.json ...]   (sem argumentos: todos)
"""
import json
import statistics
import sys
import time

from interpretador import MODELO, PASTA, carregar_destinos, interpretar, resumo


def main():
    arquivos = sys.argv[1:] or sorted((PASTA / 'testes_frases').glob('*.json'))
    destinos = carregar_destinos()
    interpretar('ponto 1', destinos, 1.0)   # carrega o modelo fora da medição
    for arquivo in arquivos:
        with open(arquivo, encoding='utf-8') as f:
            casos = json.load(f)
        acertos, perigosos, perdidos, tempos = 0, [], [], []
        for caso in casos:
            inicio = time.monotonic()
            obtido = resumo(interpretar(caso['frase'], destinos, 1.0))
            tempos.append(time.monotonic() - inicio)
            esperado = caso['esperado']
            if obtido == esperado:
                acertos += 1
            elif obtido.startswith(('ir_para', 'voltar')):
                perigosos.append((caso['frase'], esperado, obtido))   # moveria errado
            else:
                perdidos.append((caso['frase'], esperado, obtido))    # só deixaria de agir
        print(f'\n== {arquivo} | {MODELO}')
        print(f'acertos: {acertos}/{len(casos)}  moveria errado: {len(perigosos)}  '
              f'outros erros (sem movimento): {len(perdidos)}')
        print(f'tempo: mediana {statistics.median(tempos):.2f} s, máximo {max(tempos):.2f} s')
        for rotulo, lista in (('MOVERIA ERRADO', perigosos), ('sem movimento', perdidos)):
            for frase, esperado, obtido in lista:
                print(f'  [{rotulo}] "{frase}": esperado {esperado}, obtido {obtido}')


if __name__ == '__main__':
    main()

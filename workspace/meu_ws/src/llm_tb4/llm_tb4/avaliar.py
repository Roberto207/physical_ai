"""Mede o interpretador com o modelo real: acertos, erros perigosos e tempo de resposta.

Precisa do Ollama rodando. Não move o robô.
Uso, na pasta do pacote: python3 -m llm_tb4.avaliar [test/frases/ajuste.json ...]
(sem argumentos: todos)
"""
import json
import statistics
import sys
import time
from pathlib import Path

from llm_tb4 import mapa, recursos
from llm_tb4.interpretador import MODELO, carregar_destinos, interpretar, resumo


def main():
    arquivos = sys.argv[1:] or sorted(recursos.caminho('test', 'frases').glob('*.json'))
    destinos = carregar_destinos()
    mapas = Path(__file__).resolve().parents[4] / 'mapas'
    conferir = mapa.verificador(mapas / 'mapa_lab_novo.yaml')
    # Carrega o modelo fora da medição. Sem modelo não há o que medir: as recusas por falha
    # pareceriam acertos ("moveria errado: 0").
    teste = interpretar('ponto 1', destinos, 1.0)
    if teste.get('falha_modelo'):
        print(f'ERRO: o modelo {MODELO} não respondeu ({teste["motivo"]}). Nada foi medido.')
        return 2
    falhas_totais = 0
    for arquivo in arquivos:
        with open(arquivo, encoding='utf-8') as f:
            casos = json.load(f)
        acertos, falhas, perigosos, perdidos, tempos = 0, 0, [], [], []
        paradas, paradas_perdidas = 0, 0
        for caso in casos:
            inicio = time.monotonic()
            decisao = interpretar(caso['frase'], destinos, 1.0, motivo_coordenada=conferir)
            tempos.append(time.monotonic() - inicio)
            obtido, esperado = resumo(decisao), caso['esperado']
            if esperado == 'parar':
                paradas += 1
                paradas_perdidas += obtido != 'parar'
            if decisao.get('falha_modelo'):
                falhas += 1
            elif obtido in esperado.split('|'):   # "a|b": os dois resultados são aceitáveis
                acertos += 1
            elif obtido.startswith(('ir_para', 'voltar', 'sair', 'encaixar')):
                perigosos.append((caso['frase'], esperado, obtido))   # moveria errado
            else:
                perdidos.append((caso['frase'], esperado, obtido))    # só deixaria de agir
        print(f'\n== {arquivo} | {MODELO}')
        print(f'acertos: {acertos}/{len(casos)}  moveria errado: {len(perigosos)}  '
              f'outros erros (sem movimento): {len(perdidos)}')
        if paradas:
            print(f'pedidos de parar não reconhecidos: {paradas_perdidas}/{paradas}')
        if falhas:
            print(f'FALHAS DO MODELO: {falhas} (não contam como acerto nem como erro)')
        falhas_totais += falhas
        print(f'tempo: mediana {statistics.median(tempos):.2f} s, máximo {max(tempos):.2f} s')
        for rotulo, lista in (('MOVERIA ERRADO', perigosos), ('sem movimento', perdidos)):
            for frase, esperado, obtido in lista:
                print(f'  [{rotulo}] "{frase}": esperado {esperado}, obtido {obtido}')
    return 1 if falhas_totais else 0


if __name__ == '__main__':
    sys.exit(main())

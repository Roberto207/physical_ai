"""Confere um mapa recém-saído do SLAM antes de usá-lo na patrulha. Sem ROS e sem robô.

O `validar_pontos` confere as poses contra um mapa. Este comando vem antes: diz se o
próprio mapa é utilizável e mostra os números que ajudam a julgá-lo (tamanho, quanto foi
explorado e o que há na origem, onde fica a doca se o SLAM começou nela, hipótese H3).

Uso pela linha de comando:

    conferir_mapa caminho/do/mapa.yaml
    python3 -m patrulha_tb4.mapa_slam caminho/do/mapa.yaml

Códigos de saída: 0 = utilizável, 2 = recusado (ilegível ou sem nenhuma célula livre).
"""
import argparse
import sys
from collections import Counter
from dataclasses import dataclass

from patrulha_tb4.pontos import (DESCONHECIDA, LIVRE, OCUPADA, MapaInvalido, ler_mapa)

# Abaixo disto, o SLAM provavelmente mal começou (o robô quase não andou). Só um aviso:
# um laboratório pequeno num mapa grande também dá fração baixa.
FRACAO_LIVRE_BAIXA = 0.05


@dataclass(frozen=True)
class Resumo:
    largura_m: float
    altura_m: float
    resolucao: float
    fracao_livre: float
    fracao_ocupada: float
    fracao_desconhecida: float
    estado_origem: str   # livre, ocupada, desconhecida, ou fora_do_mapa

    @property
    def utilizavel(self):
        return self.fracao_livre > 0


def resumir(mapa):
    """Conta as células por estado e olha a célula de (0, 0)."""
    contagem = Counter(mapa.estado(coluna, linha)
                       for linha in range(mapa.altura) for coluna in range(mapa.largura))
    total = mapa.largura * mapa.altura
    celula = mapa.celula(0.0, 0.0)
    return Resumo(
        largura_m=mapa.largura * mapa.resolucao,
        altura_m=mapa.altura * mapa.resolucao,
        resolucao=mapa.resolucao,
        fracao_livre=contagem[LIVRE] / total,
        fracao_ocupada=contagem[OCUPADA] / total,
        fracao_desconhecida=contagem[DESCONHECIDA] / total,
        estado_origem=mapa.estado(*celula) if celula else 'fora_do_mapa')


def main(argumentos=None):
    analisador = argparse.ArgumentParser(
        prog='conferir_mapa',
        description='Diz se um mapa do SLAM (.yaml + .pgm) é utilizável, sem ROS.')
    analisador.add_argument('mapa', help='arquivo .yaml gravado pelo map_saver / slam_toolbox')
    opcoes = analisador.parse_args(argumentos)
    try:
        resumo = resumir(ler_mapa(opcoes.mapa))
    except MapaInvalido as erro:
        print(f'RECUSADO: {erro}')
        return 2
    print(f'Mapa: {opcoes.mapa}')
    print(f'  tamanho      {resumo.largura_m:.2f} m x {resumo.altura_m:.2f} m '
          f'({resumo.resolucao:.3f} m por célula)')
    print(f'  livre        {resumo.fracao_livre:6.1%}')
    print(f'  ocupada      {resumo.fracao_ocupada:6.1%}')
    print(f'  não mapeada  {resumo.fracao_desconhecida:6.1%}')
    print(f'  origem (0,0) {resumo.estado_origem}')
    if not resumo.utilizavel:
        print('RECUSADO: nenhuma célula livre. O SLAM recebeu o /scan?')
        return 2
    if resumo.fracao_livre < FRACAO_LIVRE_BAIXA:
        print('AVISO: pouca área livre. O robô percorreu o laboratório inteiro?')
    if resumo.estado_origem == 'fora_do_mapa':
        print('AVISO: a origem está fora do mapa. A pose_inicial não será (0, 0).')
    print('UTILIZÁVEL. Abra o .pgm e confira se as paredes não estão duplicadas ("fantasmas").')
    return 0


if __name__ == '__main__':
    sys.exit(main())

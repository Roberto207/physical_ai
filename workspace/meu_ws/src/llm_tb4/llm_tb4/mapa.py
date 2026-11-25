"""Confere uma coordenada pedida contra o mapa, com o validador de poses da patrulha_tb4."""
import sys
from pathlib import Path

MARGEM_M = 0.25   # a mesma do validar_pontos; o raio do robô é menor (0,175 m)
MAPA_PADRAO = '/mapas/mapa_lab_novo.yaml'


def verificador(caminho_mapa):
    """Devolve função(x, y) -> None se o ponto serve, ou o motivo. Sem mapa, recusa tudo."""
    try:
        try:
            from patrulha_tb4 import pontos
        except ImportError:   # fora do ROS: o pacote vizinho, na árvore do código
            sys.path.append(str(Path(__file__).resolve().parents[2] / 'patrulha_tb4'))
            from patrulha_tb4 import pontos
        mapa = pontos.ler_mapa(str(caminho_mapa))
    except Exception as erro:
        motivo = f'mapa indisponível ({type(erro).__name__})'
        return lambda x, y: motivo
    return lambda x, y: pontos.motivo_da_pose(mapa, x, y, MARGEM_M)

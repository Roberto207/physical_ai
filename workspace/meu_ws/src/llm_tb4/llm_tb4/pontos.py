"""Para onde ir: pontos da patrulha oficial, direção de chegada e proteção em volta da doca.

Os pontos ficam num lugar só, o patrol_loop.py da patrulha. Aqui o arquivo é lido como texto
(ast), sem ser executado, porque ele não faz parte deste pacote.
"""
import ast
import math

from llm_tb4.missao import NAVEGAR, Passo

ARQUIVO_PADRAO = '/workspace/patrulha_oficial/patrol_loop.py'
RAIO_DOCA_M = 0.5   # coordenada livre mais perto que isto é recusada (o ponto 1 fica a 0,98 m)


class PontosInvalidos(Exception):
    pass


def ler_pontos(caminho):
    """Devolve (doca, pontos) a partir de DOCA e PONTOS do patrol_loop.py."""
    try:
        with open(caminho, encoding='utf-8') as arquivo:
            corpo = ast.parse(arquivo.read()).body
        valores = {n.targets[0].id: n.value for n in corpo
                   if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
        doca = tuple(float(v) for v in ast.literal_eval(valores['DOCA']))
        pontos = tuple(tuple(float(v) for v in p) for p in ast.literal_eval(valores['PONTOS']))
    except (OSError, SyntaxError, KeyError, ValueError, TypeError) as erro:
        raise PontosInvalidos(f'não li DOCA e PONTOS de {caminho}: {erro!r}')
    if len(doca) != 2 or not pontos or any(len(p) != 2 for p in pontos):
        raise PontosInvalidos(f'DOCA ou PONTOS com formato inesperado em {caminho}')
    return doca, pontos


def direcao(de, para):
    """Graus no referencial do mapa olhando de um ponto para outro."""
    return math.degrees(math.atan2(para[1] - de[1], para[0] - de[0]))


class Rota:
    def __init__(self, doca, pontos, destinos):
        faltam = [n for n, d in destinos.items() if not 1 <= d['ponto'] <= len(pontos)]
        if faltam:
            raise PontosInvalidos(f'destinos sem ponto correspondente: {faltam}')
        self.doca, self.pontos, self.destinos = doca, pontos, destinos

    def destino(self, acao):
        """Passo de navegação para uma ação já validada."""
        argumentos = acao['argumentos']
        if acao['acao'] == 'ir_para':
            numero = self.destinos[argumentos['local']]['ponto']
            x, y = self.pontos[numero - 1]
            # Como na patrulha oficial: chega olhando para o ponto seguinte.
            graus = direcao((x, y), self.pontos[numero % len(self.pontos)])
            nome = f'ir ao ponto {numero}'
        else:
            x, y = argumentos['x'], argumentos['y']
            graus = argumentos['graus'] if argumentos['graus'] is not None else 0.0
            nome = f'ir a x={x:g} y={y:g}'
        return Passo(NAVEGAR, nome, float(x), float(y), float(graus), exige_bateria=True)

    def aproximacao(self):
        """Ponto 1, virado para a doca. Vale com bateria baixa."""
        x, y = self.pontos[0]
        return Passo(NAVEGAR, 'aproximar da doca', x, y, direcao((x, y), self.doca))

    def verificador(self, no_mapa):
        """Soma à conferência do mapa a proteção em volta da doca."""
        def motivo(x, y):
            problema = no_mapa(x, y)
            if problema:
                return problema
            if math.dist((x, y), self.doca) < RAIO_DOCA_M:
                return 'perto_da_doca (peça "volte para a doca")'
            return None
        return motivo

    def problemas(self, no_mapa):
        """Pontos da patrulha que o mapa não aceita."""
        return [(i, no_mapa(*p)) for i, p in enumerate(self.pontos, 1) if no_mapa(*p)]

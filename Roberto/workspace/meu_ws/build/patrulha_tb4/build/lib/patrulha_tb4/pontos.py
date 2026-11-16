"""Valida as poses da configuração contra o mapa (VAL-01 a VAL-03). Sem ROS e sem robô.

Lê o par `.yaml` + `.pgm` no formato que o `map_saver` do Nav2 grava. É o mesmo formato
de um mapa feito com SLAM no laboratório, então serve para qualquer mapa nosso.

Uso pela linha de comando:

    validar_pontos caminho/da/configuracao.yaml
    python3 -m patrulha_tb4.pontos caminho/da/configuracao.yaml
"""
import argparse
import math
import os
import sys
from dataclasses import dataclass

import yaml

from patrulha_tb4.config import ConfigInvalida, carregar

LIVRE, OCUPADA, DESCONHECIDA = 'livre', 'ocupada', 'desconhecida'
CINZA_NAO_MAPEADO = 205

FORA_DO_MAPA = 'fora_do_mapa'
CELULA_OCUPADA = 'celula_ocupada'
CELULA_DESCONHECIDA = 'celula_desconhecida'
PERTO_DE_OBSTACULO = 'perto_de_obstaculo'


class MapaInvalido(Exception):
    pass


@dataclass(frozen=True)
class Mapa:
    largura: int
    altura: int
    maximo: int
    pixels: bytes  # uma amostra por célula, linha de cima primeiro (como no .pgm)
    resolucao: float
    origem_x: float
    origem_y: float
    origem_yaw: float
    negate: bool
    limiar_ocupado: float
    limiar_livre: float

    def celula(self, x, y):
        """Converte (x, y) em metros para (coluna, linha a partir de baixo), ou None se cair fora."""
        dx, dy = x - self.origem_x, y - self.origem_y
        cos, sen = math.cos(-self.origem_yaw), math.sin(-self.origem_yaw)
        mx, my = dx * cos - dy * sen, dx * sen + dy * cos
        coluna, linha = math.floor(mx / self.resolucao), math.floor(my / self.resolucao)
        if 0 <= coluna < self.largura and 0 <= linha < self.altura:
            return coluna, linha
        return None

    def estado(self, coluna, linha):
        """Livre, ocupada ou desconhecida, pela conta do map_server (modo trinary).

        Uma cautela a mais: o cinza 205 é o valor que o `map_saver` grava para "não
        mapeado". Com `free_thresh: 0.25`, a conta pura o leria como livre (ocupação de
        0,196). Aqui ele é sempre desconhecido: na dúvida, o robô não vai para lá.
        """
        bruto = self.pixels[(self.altura - 1 - linha) * self.largura + coluna]
        if bruto == CINZA_NAO_MAPEADO and self.maximo == 255:
            return DESCONHECIDA
        valor = bruto / self.maximo
        ocupacao = valor if self.negate else 1.0 - valor
        if ocupacao > self.limiar_ocupado:
            return OCUPADA
        if ocupacao < self.limiar_livre:
            return LIVRE
        return DESCONHECIDA


def ler_pgm(caminho):
    """Lê um PGM binário (P5) ou em texto (P2), com 8 bits por célula."""
    with open(caminho, 'rb') as arquivo:
        dados = arquivo.read()
    campos, posicao = [], 0
    while len(campos) < 4:
        while posicao < len(dados) and dados[posicao:posicao + 1].isspace():
            posicao += 1
        if posicao >= len(dados):
            raise MapaInvalido(f'cabeçalho incompleto em {caminho}')
        if dados[posicao:posicao + 1] == b'#':
            while posicao < len(dados) and dados[posicao:posicao + 1] != b'\n':
                posicao += 1
            continue
        fim = posicao
        while fim < len(dados) and not dados[fim:fim + 1].isspace():
            fim += 1
        campos.append(dados[posicao:fim])
        posicao = fim
    tipo = campos[0]
    try:
        largura, altura, maximo = (int(campo) for campo in campos[1:])
    except ValueError:
        raise MapaInvalido(f'cabeçalho inválido em {caminho}')
    if largura <= 0 or altura <= 0 or not 0 < maximo <= 255:
        raise MapaInvalido(f'dimensões ou profundidade não suportadas em {caminho}')
    if tipo == b'P5':
        pixels = dados[posicao + 1:posicao + 1 + largura * altura]
    elif tipo == b'P2':
        try:
            pixels = bytes(int(valor) for valor in dados[posicao:].split()[:largura * altura])
        except ValueError:
            raise MapaInvalido(f'valores inválidos em {caminho}')
    else:
        raise MapaInvalido(f'formato {tipo!r} não suportado (esperado P5 ou P2)')
    if len(pixels) != largura * altura:
        raise MapaInvalido(f'faltam células em {caminho}')
    return largura, altura, maximo, pixels


def ler_mapa(caminho_yaml):
    """Lê o `.yaml` do mapa e a imagem que ele aponta."""
    try:
        with open(caminho_yaml, 'r', encoding='utf-8') as arquivo:
            meta = yaml.safe_load(arquivo)
    except (OSError, yaml.YAMLError) as erro:
        raise MapaInvalido(f'não consegui ler {caminho_yaml}: {erro}')
    try:
        imagem = meta['image']
        resolucao = float(meta['resolution'])
        origem = [float(valor) for valor in meta['origin']]
    except (KeyError, TypeError, ValueError) as erro:
        raise MapaInvalido(f'campo ausente ou inválido em {caminho_yaml}: {erro}')
    modo = meta.get('mode', 'trinary')
    if modo != 'trinary':
        raise MapaInvalido(f'modo {modo!r} não suportado (esperado trinary)')
    if resolucao <= 0 or len(origem) < 2:
        raise MapaInvalido(f'resolução ou origem inválida em {caminho_yaml}')
    if not os.path.isabs(imagem):
        imagem = os.path.join(os.path.dirname(os.path.abspath(caminho_yaml)), imagem)
    if not imagem.lower().endswith('.pgm'):
        raise MapaInvalido(f'imagem {imagem} não é .pgm')
    try:
        largura, altura, maximo, pixels = ler_pgm(imagem)
    except OSError as erro:
        raise MapaInvalido(f'não consegui ler {imagem}: {erro}')
    return Mapa(largura=largura, altura=altura, maximo=maximo, pixels=pixels,
                resolucao=resolucao, origem_x=origem[0], origem_y=origem[1],
                origem_yaw=origem[2] if len(origem) > 2 else 0.0,
                negate=bool(meta.get('negate', 0)),
                limiar_ocupado=float(meta.get('occupied_thresh', 0.65)),
                limiar_livre=float(meta.get('free_thresh', 0.25)))


def motivo_da_pose(mapa, x, y, margem_m):
    """Devolve o motivo que reprova a pose (VAL-02), ou None se ela serve."""
    celula = mapa.celula(x, y)
    if celula is None:
        return FORA_DO_MAPA
    coluna, linha = celula
    estado = mapa.estado(coluna, linha)
    if estado == OCUPADA:
        return CELULA_OCUPADA
    if estado == DESCONHECIDA:
        return CELULA_DESCONHECIDA
    alcance = math.ceil(margem_m / mapa.resolucao)
    for dl in range(-alcance, alcance + 1):
        for dc in range(-alcance, alcance + 1):
            c, l = coluna + dc, linha + dl
            if not (0 <= c < mapa.largura and 0 <= l < mapa.altura):
                continue
            if math.hypot(dc, dl) * mapa.resolucao < margem_m and mapa.estado(c, l) == OCUPADA:
                return PERTO_DE_OBSTACULO
    return None


def validar_poses(config, mapa):
    """Lista de (nome da pose, motivo) para cada pose reprovada. Vazia se todas servem."""
    problemas = []
    for pose in config.poses_nomeadas():
        motivo = motivo_da_pose(mapa, pose.x, pose.y, config.margem_obstaculo_m)
        if motivo:
            problemas.append((pose.nome, motivo))
    return problemas


def validar_configuracao(caminho):
    """VAL-01: carrega a configuração e o mapa e confere tudo.

    Devolve (config, problemas). Levanta ConfigInvalida se a configuração ou o mapa
    não puderem ser lidos.
    """
    config = carregar(caminho)
    try:
        mapa = ler_mapa(config.mapa)
    except MapaInvalido as erro:
        raise ConfigInvalida('mapa_invalido', str(erro))
    return config, validar_poses(config, mapa)


def main(argumentos=None):
    analisador = argparse.ArgumentParser(
        prog='validar_pontos',
        description='Confere a configuração da patrulha e cada pose contra o mapa, sem ROS.')
    analisador.add_argument('config', help='arquivo YAML da patrulha')
    opcoes = analisador.parse_args(argumentos)
    try:
        config, problemas = validar_configuracao(opcoes.config)
    except ConfigInvalida as erro:
        print(f'REPROVADA: {erro}')
        return 2
    print(f'Mapa: {config.mapa}')
    reprovadas = dict(problemas)
    for pose in config.poses_nomeadas():
        situacao = reprovadas.get(pose.nome, 'ok')
        print(f'  {pose.nome:<18} x={pose.x:8.3f} y={pose.y:8.3f}  {situacao}')
    if problemas:
        print(f'REPROVADA: {len(problemas)} pose(s) com problema.')
        return 2
    print('APROVADA: todas as poses estão em célula livre e longe de obstáculo.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Carrega e confere a configuração da patrulha (PAT-01, PAT-21, VAL-04). Sem ROS.

Tudo o que muda de um ambiente para outro (mapa, pontos, pose inicial, aproximação da
doca, limites de bateria e tempos) vem deste arquivo YAML, e de nenhum outro lugar.
"""
import hashlib
import math
import os
from dataclasses import dataclass
from typing import Optional, Tuple

import yaml

AMBIENTES = ('leve', 'gazebo', 'real')
MODELOS = ('standard', 'lite')
MODOS_BATERIA = ('absoluto', 'relativo')

# Padrão de bateria_perdida_s por ambiente (PAT-18). No real não há padrão: o valor
# sai da medição da etapa 1 do kit de campo e precisa estar no arquivo.
BATERIA_PERDIDA_PADRAO_S = {'leve': 10.0, 'gazebo': 30.0}


class ConfigInvalida(Exception):
    """A configuração não serve para patrulhar. `motivo` vai para o evento config_invalida."""

    def __init__(self, motivo, detalhe=''):
        super().__init__(f'{motivo}: {detalhe}' if detalhe else motivo)
        self.motivo = motivo
        self.detalhe = detalhe


@dataclass(frozen=True)
class Pose:
    nome: str
    x: float
    y: float
    yaw_graus: float


@dataclass(frozen=True)
class Limites:
    alta: float
    baixa: float
    critica: float

    def como_dict(self):
        return {'alta': self.alta, 'baixa': self.baixa, 'critica': self.critica}


@dataclass(frozen=True)
class Deltas:
    alta: float
    baixa: float
    critica: float


@dataclass(frozen=True)
class Tempos:
    espera_bateria_s: float
    confirma_dock_s: float
    cancelar_s: float
    bateria_perdida_s: float
    destino_s: float
    servidor_s: float
    encerrar_s: float
    sem_relogio_s: float


@dataclass(frozen=True)
class Config:
    ambiente: str
    modelo: str
    mapa: str
    pose_inicial: Pose
    aproximacao_doca: Pose
    pontos: Tuple[Pose, ...]
    modo_bateria: str
    limites: Optional[Limites]  # None no modo relativo, até a primeira bateria (PAT-21)
    deltas: Deltas
    tempos: Tempos
    falhas_seguidas: int
    tentativas_dock: int
    margem_obstaculo_m: float
    caminho: str
    hash_config: str

    @property
    def usa_tempo_simulado(self):
        """AMB-02: relógio simulado no leve e no gazebo, relógio real no robô."""
        return self.ambiente in ('leve', 'gazebo')

    def poses_nomeadas(self):
        """Todas as poses que o robô pode receber como destino, mais a pose inicial."""
        return (self.pose_inicial, self.aproximacao_doca) + self.pontos


def limites_validos(limites):
    """VAL-04: números finitos com 0 < critica < baixa < alta <= 1."""
    valores = (limites.critica, limites.baixa, limites.alta)
    if not all(_e_numero(v) and math.isfinite(v) for v in valores):
        return False
    return 0 < limites.critica < limites.baixa < limites.alta <= 1


def calcular_limites(deltas, b0):
    """PAT-21: limites a partir da primeira leitura de bateria. Não valida (ver VAL-04)."""
    return Limites(alta=b0 - deltas.alta, baixa=b0 - deltas.baixa, critica=b0 - deltas.critica)


def hash_arquivo(caminho):
    with open(caminho, 'rb') as arquivo:
        return hashlib.sha256(arquivo.read()).hexdigest()


def carregar(caminho):
    """Lê o YAML e devolve a Config, ou levanta ConfigInvalida com o motivo."""
    caminho = os.path.abspath(os.path.expanduser(str(caminho)))
    try:
        with open(caminho, 'rb') as arquivo:
            bruto = arquivo.read()
    except OSError as erro:
        raise ConfigInvalida('arquivo_ilegivel', str(erro))
    try:
        dados = yaml.safe_load(bruto)
    except yaml.YAMLError as erro:
        raise ConfigInvalida('yaml_invalido', str(erro))
    if not isinstance(dados, dict) or not isinstance(dados.get('patrulha'), dict):
        raise ConfigInvalida('campo_faltando', 'patrulha')
    return montar(dados['patrulha'], caminho, hashlib.sha256(bruto).hexdigest())


def montar(raiz, caminho='', hash_config=''):
    """Confere o conteúdo já lido do YAML (a seção `patrulha`)."""
    ambiente = _escolha(raiz, 'ambiente', AMBIENTES, 'ambiente_invalido')
    modelo = _escolha(raiz, 'modelo', MODELOS, 'modelo_invalido', padrao='standard')

    mapa = raiz.get('mapa')
    if not isinstance(mapa, str) or not mapa.strip():
        raise ConfigInvalida('campo_faltando', 'mapa')
    mapa = os.path.expandvars(os.path.expanduser(mapa))
    if not os.path.isabs(mapa):
        mapa = os.path.normpath(os.path.join(os.path.dirname(caminho), mapa))

    pose_inicial = _pose(raiz.get('pose_inicial'), 'pose_inicial')
    aproximacao = _pose(raiz.get('aproximacao_doca'), 'aproximacao_doca')
    lista = raiz.get('pontos')
    if not isinstance(lista, list) or not lista:
        raise ConfigInvalida('campo_faltando', 'pontos')
    pontos = tuple(_pose(item, f'pontos[{i}]') for i, item in enumerate(lista))

    bateria = raiz.get('bateria') or {}
    if not isinstance(bateria, dict):
        raise ConfigInvalida('campo_invalido', 'bateria')
    modo = bateria.get('modo', 'absoluto')
    if modo not in MODOS_BATERIA:
        raise ConfigInvalida('modo_invalido', str(modo))
    deltas = Deltas(alta=bateria.get('delta_alta', 0.005),
                    baixa=bateria.get('delta_baixa', 0.01),
                    critica=bateria.get('delta_critica', 0.02))
    if modo == 'absoluto':
        limites = Limites(alta=bateria.get('alta', 0.95),
                          baixa=bateria.get('baixa', 0.20),
                          critica=bateria.get('critica', 0.10))
        if not limites_validos(limites):
            raise ConfigInvalida('limites_invalidos', str(limites.como_dict()))
    else:
        limites = None
        valores = (deltas.alta, deltas.baixa, deltas.critica)
        em_ordem = all(_e_numero(v) and math.isfinite(v) for v in valores) \
            and 0 <= deltas.alta < deltas.baixa < deltas.critica
        if not em_ordem:
            raise ConfigInvalida('limites_invalidos', f'deltas {valores}')

    tempos_brutos = raiz.get('tempos') or {}
    if not isinstance(tempos_brutos, dict):
        raise ConfigInvalida('campo_invalido', 'tempos')
    perdida = tempos_brutos.get('bateria_perdida_s', BATERIA_PERDIDA_PADRAO_S.get(ambiente))
    if perdida is None:
        raise ConfigInvalida('campo_faltando', 'tempos.bateria_perdida_s (obrigatório no real)')
    tempos = Tempos(
        espera_bateria_s=_positivo(tempos_brutos, 'espera_bateria_s', 30.0),
        confirma_dock_s=_positivo(tempos_brutos, 'confirma_dock_s', 5.0),
        cancelar_s=_positivo(tempos_brutos, 'cancelar_s', 2.0),
        bateria_perdida_s=_positivo({'bateria_perdida_s': perdida}, 'bateria_perdida_s', None),
        destino_s=_positivo(tempos_brutos, 'destino_s', 120.0),
        servidor_s=_positivo(tempos_brutos, 'servidor_s', 30.0),
        encerrar_s=_positivo(tempos_brutos, 'encerrar_s', 3.0),
        sem_relogio_s=_positivo(tempos_brutos, 'sem_relogio_s', 10.0),
    )

    limites_gerais = raiz.get('limites') or {}
    validacao = raiz.get('validacao') or {}
    if not isinstance(limites_gerais, dict) or not isinstance(validacao, dict):
        raise ConfigInvalida('campo_invalido', 'limites ou validacao')
    falhas = _inteiro_positivo(limites_gerais, 'falhas_seguidas', 3)
    tentativas = _inteiro_positivo(limites_gerais, 'tentativas_dock', 3)
    margem = validacao.get('margem_obstaculo_m', 0.25)
    if not _e_numero(margem) or not math.isfinite(margem) or margem < 0:
        raise ConfigInvalida('campo_invalido', 'validacao.margem_obstaculo_m')

    return Config(ambiente=ambiente, modelo=modelo, mapa=mapa, pose_inicial=pose_inicial,
                  aproximacao_doca=aproximacao, pontos=pontos, modo_bateria=modo,
                  limites=limites, deltas=deltas, tempos=tempos, falhas_seguidas=falhas,
                  tentativas_dock=tentativas, margem_obstaculo_m=float(margem),
                  caminho=caminho, hash_config=hash_config)


def _e_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _escolha(raiz, campo, opcoes, motivo, padrao=None):
    valor = raiz.get(campo, padrao)
    if valor is None:
        raise ConfigInvalida('campo_faltando', campo)
    if valor not in opcoes:
        raise ConfigInvalida(motivo, str(valor))
    return valor


def _pose(bruto, nome):
    if not isinstance(bruto, dict):
        raise ConfigInvalida('campo_faltando', nome)
    valores = []
    for campo in ('x', 'y', 'yaw_graus'):
        valor = bruto.get(campo)
        if not _e_numero(valor) or not math.isfinite(valor):
            raise ConfigInvalida('pose_invalida', f'{nome}.{campo}')
        valores.append(float(valor))
    return Pose(nome, *valores)


def _positivo(origem, campo, padrao):
    valor = origem.get(campo, padrao)
    if not _e_numero(valor) or not math.isfinite(valor) or valor <= 0:
        raise ConfigInvalida('campo_invalido', f'tempos.{campo}')
    return float(valor)


def _inteiro_positivo(origem, campo, padrao):
    valor = origem.get(campo, padrao)
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < 1:
        raise ConfigInvalida('campo_invalido', f'limites.{campo}')
    return valor

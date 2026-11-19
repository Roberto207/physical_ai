"""A decisão da patrulha: uma máquina de estados pura, sem ROS e sem robô (PAT-03 a PAT-22).

O nó ROS só lê os sensores, monta uma `Entrada`, chama `decidir()` e executa as ações
devolvidas. Como aqui não há relógio, rede nem robô, cada situação difícil de provocar
num simulador (a bateria cai no meio do trecho, o dock falha duas vezes, a bateria some)
vira um teste de milissegundos.

Evolução de `workspace/exemplos/decisao_patrulha.py`.
"""
from dataclasses import dataclass, replace
from typing import Optional

from patrulha_tb4.config import Limites, calcular_limites, limites_validos

# Fases (o campo `estado` do log).
INICIANDO = 'iniciando'
SAINDO_DOCA = 'saindo_doca'
PATRULHANDO = 'patrulhando'
INDO_DOCA = 'indo_doca'
ENCAIXANDO = 'encaixando'
CARREGANDO = 'carregando'
ENCERRANDO = 'encerrando'

# Ações que o nó executa.
DESTINO = 'destino'          # ('destino', índice do ponto)
APROXIMACAO = 'aproximacao'  # ('aproximacao',): destino de aproximação da doca
DOCK = 'dock'
UNDOCK = 'undock'
CANCELAR = 'cancelar'        # cancela a ação ativa
ENCERRAR = 'encerrar'        # ('encerrar', código de saída)

# Resultado de uma ação terminada.
SUCESSO = 'sucesso'
FALHOU = 'falhou'
CANCELADO = 'cancelado'

# Motivos da ida à doca.
POR_BATERIA = 'bateria'
POR_FALHAS = 'falhas_seguidas'

# PAT-05: o nó chama decidir() pelo menos 1 vez por segundo.
PERIODO_S = 1.0

CODIGO_ENCERRADO = 0
CODIGO_CONFIG = 2
CODIGO_SEM_BATERIA = 3
CODIGO_DOCK = 4
CODIGO_UNDOCK = 5
CODIGO_FORA_DA_DOCA = 6
CODIGO_FALHAS = 7
CODIGO_SERVIDOR = 8
CODIGO_SEM_RELOGIO = 9


@dataclass(frozen=True)
class Resultado:
    acao: str                      # destino, aproximacao, dock ou undock
    status: str                    # sucesso, falhou ou cancelado
    codigo: Optional[object] = None  # código do Nav2 ou da ação, para o log


@dataclass(frozen=True)
class Entrada:
    """O que o nó sabe neste instante."""

    parede: float                          # tempo de relógio (time.time)
    agora: Optional[float]                 # relógio do ROS; None se o tempo simulado não chegou
    bateria: Optional[float] = None        # última fração recebida, de 0 a 1
    t_bateria: Optional[float] = None      # relógio do ROS na chegada da última bateria
    na_base: Optional[bool] = None         # is_docked do último /dock_status
    servidores_ok: bool = False            # navigate_to_pose, dock e undock disponíveis
    resultado: Optional[Resultado] = None  # resultado da ação ativa, se ela terminou
    sinal: bool = False                    # chegou SIGINT ou SIGTERM
    usa_sim_time: bool = False
    parede_relogio: Optional[float] = None  # tempo de relógio da última mensagem de /clock


@dataclass(frozen=True)
class Estado:
    fase: str = INICIANDO
    parede_inicio: Optional[float] = None
    t_inicio: Optional[float] = None
    limites: Optional[Limites] = None
    indice: int = 0                 # ponto de patrulha atual
    voltas: int = 0
    falhas_seguidas: int = 0
    acao: Optional[str] = None      # ação ativa
    t_acao: Optional[float] = None  # relógio do ROS no envio da ação ativa
    motivo_doca: Optional[str] = None
    tentativas_dock: int = 0
    t_resultado_dock: Optional[float] = None  # espera do is_docked depois do dock (PAT-09)
    perda_gravada: bool = False     # bateria_perdida já gravado nesta perda (PAT-18)
    codigo_saida: Optional[int] = None


@dataclass(frozen=True)
class Saida:
    estado: Estado
    acoes: tuple
    eventos: tuple


class _Passo:
    """Acumula as mudanças de estado, as ações e os eventos de uma chamada."""

    def __init__(self, estado):
        self.estado = estado
        self.acoes = []
        self.eventos = []

    def mudar(self, **campos):
        self.estado = replace(self.estado, **campos)

    def evento(self, nome, **campos):
        self.eventos.append({'evento': nome, **campos})

    def cancelar(self):
        """Pede o cancelamento da ação ativa, se houver."""
        if self.estado.acao is not None:
            self.acoes.append((CANCELAR,))
            self.mudar(acao=None, t_acao=None)

    def enviar(self, agora, acao, *argumentos):
        self.acoes.append((acao,) + argumentos)
        self.mudar(acao=acao, t_acao=agora)

    def encerrar(self, codigo, evento=None, **campos):
        self.cancelar()
        if evento:
            self.evento(evento, **campos)
        self.acoes.append((ENCERRAR, codigo))
        self.mudar(fase=ENCERRANDO, codigo_saida=codigo, t_resultado_dock=None)
        return self.saida()

    def saida(self):
        return Saida(self.estado, tuple(self.acoes), tuple(self.eventos))


def decidir(estado, entrada, cfg):
    """Devolve o novo estado, as ações a executar (em ordem) e os eventos a gravar."""
    p = _Passo(estado)
    if estado.fase == ENCERRANDO:
        return p.saida()
    if estado.parede_inicio is None:
        p.mudar(parede_inicio=entrada.parede)

    # PAT-15: pedido de encerramento.
    if entrada.sinal:
        return p.encerrar(CODIGO_ENCERRADO, 'encerrado')

    # PAT-22: sem /clock, nenhum tempo-limite simulado venceria. Conta em tempo de relógio.
    if entrada.usa_sim_time:
        referencia = entrada.parede_relogio
        if referencia is None:
            referencia = p.estado.parede_inicio
        if entrada.parede - referencia > cfg.tempos.sem_relogio_s:
            return p.encerrar(CODIGO_SEM_RELOGIO, 'sem_relogio')

    if entrada.agora is None:
        return p.saida()
    if p.estado.t_inicio is None:
        p.mudar(t_inicio=entrada.agora)

    perdida = _bateria_perdida(entrada, cfg)
    if not perdida and p.estado.perda_gravada:
        p.mudar(perda_gravada=False)  # chegou mensagem nova: o evento pode voltar (PAT-18)

    fase = p.estado.fase
    if fase == INICIANDO:
        return _iniciando(p, entrada, cfg, perdida)
    if fase == SAINDO_DOCA:
        return _saindo_doca(p, entrada, cfg, perdida)
    if fase == PATRULHANDO:
        return _patrulhando(p, entrada, cfg, perdida)
    if fase == INDO_DOCA:
        return _indo_doca(p, entrada, cfg, perdida)
    if fase == ENCAIXANDO:
        return _encaixando(p, entrada, cfg, perdida)
    if fase == CARREGANDO:
        return _carregando(p, entrada, cfg, perdida)
    raise ValueError(f'fase desconhecida: {fase}')


def _bateria_perdida(entrada, cfg):
    if entrada.t_bateria is None:
        return False
    return entrada.agora - entrada.t_bateria > cfg.tempos.bateria_perdida_s


def _idade_da_bateria(entrada):
    """Há quanto tempo chegou a bateria que disparou a reação (para conferir o PAT-06)."""
    if entrada.t_bateria is None:
        return None
    return f'idade_bateria_s={entrada.agora - entrada.t_bateria:.3f}'


def _resultado_de(entrada, acao):
    if entrada.resultado is not None and entrada.resultado.acao == acao:
        return entrada.resultado
    return None


def _gravar_perda(p, **campos):
    """PAT-18: grava bateria_perdida uma vez por perda."""
    if not p.estado.perda_gravada:
        p.evento('bateria_perdida', **campos)
        p.mudar(perda_gravada=True)


def _ir_para_doca(p, entrada, motivo):
    """Cancela o que estiver em andamento e envia o destino de aproximação da doca."""
    if p.estado.acao == DESTINO:
        p.evento('destino_cancelado', ponto=p.estado.indice)
    p.cancelar()
    p.evento('destino_enviado', detalhe=f'aproximacao_doca:{motivo}')
    p.enviar(entrada.agora, APROXIMACAO)
    p.mudar(fase=INDO_DOCA, motivo_doca=motivo, t_resultado_dock=None)
    return p.saida()


def _iniciando(p, entrada, cfg, perdida):
    """Sequência de início: servidores e primeira bateria, limites, doca e undock."""
    espera = entrada.agora - p.estado.t_inicio

    # PAT-03 e PAT-04: nenhuma ação antes da primeira bateria.
    if entrada.bateria is None and espera > cfg.tempos.espera_bateria_s:
        return p.encerrar(CODIGO_SEM_BATERIA, 'sem_bateria')
    # PAT-20: servidores de ação.
    if not entrada.servidores_ok and espera > cfg.tempos.servidor_s:
        return p.encerrar(CODIGO_SERVIDOR, 'servidor_indisponivel', detalhe='acoes')
    if entrada.bateria is None or not entrada.servidores_ok:
        return p.saida()

    if p.estado.limites is None:
        if cfg.modo_bateria == 'relativo':
            # PAT-21 e PAT-21b: limites calculados uma vez, da primeira leitura.
            limites = calcular_limites(cfg.deltas, entrada.bateria)
            p.evento('limites_bateria', b0=entrada.bateria, limites=limites.como_dict())
            if not limites_validos(limites):  # segunda checagem do VAL-04
                return p.encerrar(CODIGO_CONFIG, 'config_invalida', detalhe='limites_invalidos')
        else:
            limites = cfg.limites
        p.mudar(limites=limites)

    # PAT-18b: na doca e sem bateria nova.
    if perdida:
        return p.encerrar(CODIGO_SEM_BATERIA, 'bateria_perdida', detalhe='na_doca')

    # PAT-17: só começa na doca. Sem nenhum /dock_status, trata como interface indisponível.
    if entrada.na_base is None:
        if espera > cfg.tempos.servidor_s:
            return p.encerrar(CODIGO_SERVIDOR, 'servidor_indisponivel', detalhe='dock_status')
        return p.saida()
    if not entrada.na_base:
        return p.encerrar(CODIGO_FORA_DA_DOCA, 'fora_da_doca')

    # PAT-12: na doca com a bateria abaixo de `alta`, espera carregar antes do undock.
    if entrada.bateria >= p.estado.limites.alta:
        p.mudar(fase=SAINDO_DOCA)
        p.enviar(entrada.agora, UNDOCK)
    else:
        p.mudar(fase=CARREGANDO)
    return p.saida()


def _carregando(p, entrada, cfg, perdida):
    limites = p.estado.limites
    # PAT-18b.
    if perdida:
        return p.encerrar(CODIGO_SEM_BATERIA, 'bateria_perdida', detalhe='na_doca')
    # Saiu da doca sem a gente mandar (alguém empurrou, ou o encaixe soltou): volta a encaixar.
    if entrada.na_base is False:
        return _ir_para_doca(p, entrada, p.estado.motivo_doca or POR_BATERIA)
    # PAT-12 e PAT-13.
    if entrada.bateria is not None and entrada.bateria >= limites.alta:
        p.evento('carga_completa')
        p.mudar(falhas_seguidas=0, motivo_doca=None, fase=SAINDO_DOCA)
        p.enviar(entrada.agora, UNDOCK)
    return p.saida()


def _saindo_doca(p, entrada, cfg, perdida):
    limites = p.estado.limites
    if perdida:
        if entrada.na_base is False:
            # PAT-18: fora da doca, com o undock em andamento.
            _gravar_perda(p)
            return _ir_para_doca(p, entrada, POR_BATERIA)
        return p.encerrar(CODIGO_SEM_BATERIA, 'bateria_perdida', detalhe='na_doca')  # PAT-18b

    resultado = _resultado_de(entrada, UNDOCK)
    if resultado is not None:
        p.mudar(acao=None, t_acao=None)
        if resultado.status != SUCESSO:
            # PAT-16.
            return p.encerrar(CODIGO_UNDOCK, 'undock_falhou', resultado=resultado.codigo)
        p.evento('undock_ok', resultado=resultado.codigo)
        p.mudar(fase=PATRULHANDO)
        return _patrulhando(p, replace(entrada, resultado=None), cfg, perdida)

    # PAT-14: crítica, fora da doca e sem estar indo a ela.
    if entrada.na_base is False and entrada.bateria < limites.critica:
        p.evento('bateria_critica', detalhe=_idade_da_bateria(entrada))
        return _ir_para_doca(p, entrada, POR_BATERIA)
    return p.saida()


def _patrulhando(p, entrada, cfg, perdida):
    limites = p.estado.limites
    em_andamento = p.estado.acao == DESTINO

    if em_andamento:
        resultado = _resultado_de(entrada, DESTINO)
        estourou = entrada.agora - p.estado.t_acao > cfg.tempos.destino_s
        if resultado is not None:
            p.mudar(acao=None, t_acao=None)
            if resultado.status == SUCESSO:
                p.evento('destino_ok', ponto=p.estado.indice, resultado=resultado.codigo)
                p.mudar(falhas_seguidas=0)
            else:
                # PAT-07: destino falho.
                p.evento('destino_falhou', ponto=p.estado.indice, resultado=resultado.codigo)
                p.mudar(falhas_seguidas=p.estado.falhas_seguidas + 1)
            _avancar(p, cfg)
            em_andamento = False
        elif estourou:
            # PAT-19: passou do tempo, cancela e conta como destino falho.
            p.evento('destino_falhou', ponto=p.estado.indice, resultado='tempo_esgotado')
            p.cancelar()
            p.mudar(falhas_seguidas=p.estado.falhas_seguidas + 1)
            _avancar(p, cfg)
            em_andamento = False

    # PAT-18: a bateria sumiu, fora da doca.
    if perdida:
        _gravar_perda(p)
        return _ir_para_doca(p, entrada, POR_BATERIA)
    # PAT-14 prevalece sobre o PAT-06.
    if entrada.bateria < limites.critica:
        p.evento('bateria_critica', detalhe=_idade_da_bateria(entrada))
        return _ir_para_doca(p, entrada, POR_BATERIA)
    # PAT-06.
    if entrada.bateria < limites.baixa:
        p.evento('bateria_baixa', detalhe=_idade_da_bateria(entrada))
        return _ir_para_doca(p, entrada, POR_BATERIA)
    # PAT-08: destinos falhos seguidos.
    if p.estado.falhas_seguidas >= cfg.falhas_seguidas:
        return _ir_para_doca(p, entrada, POR_FALHAS)
    # PAT-07b e PAT-13: próximo ponto, ou o mesmo ponto na volta da recarga.
    if not em_andamento:
        p.evento('destino_enviado', ponto=p.estado.indice)
        p.enviar(entrada.agora, DESTINO, p.estado.indice)
    return p.saida()


def _avancar(p, cfg):
    """Passa ao próximo ponto. Fechar a lista conta uma volta."""
    proximo = p.estado.indice + 1
    if proximo >= len(cfg.pontos):
        p.mudar(indice=0, voltas=p.estado.voltas + 1)
    else:
        p.mudar(indice=proximo)


def _indo_doca(p, entrada, cfg, perdida):
    # PAT-18: já está indo à doca, então segue. Só registra a perda.
    if perdida:
        _gravar_perda(p)
    resultado = _resultado_de(entrada, APROXIMACAO)
    if resultado is None:
        return p.saida()
    p.mudar(acao=None, t_acao=None, tentativas_dock=p.estado.tentativas_dock + 1)
    if resultado.status != SUCESSO:
        # Não chegou à frente da doca: conta como uma tentativa de dock que não deu certo.
        return _dock_nao_confirmado(p, entrada, cfg, 'aproximacao_falhou', resultado.codigo)
    p.enviar(entrada.agora, DOCK)
    p.mudar(fase=ENCAIXANDO, t_resultado_dock=None)
    return p.saida()


def _encaixando(p, entrada, cfg, perdida):
    if perdida:
        _gravar_perda(p)
    if p.estado.t_resultado_dock is None:
        resultado = _resultado_de(entrada, DOCK)
        if resultado is None:
            return p.saida()
        p.mudar(acao=None, t_acao=None)
        if resultado.status != SUCESSO:
            return _dock_nao_confirmado(p, entrada, cfg, f'resultado_{resultado.status}',
                                        resultado.codigo)
        p.mudar(t_resultado_dock=entrada.agora)

    # PAT-09: a ação deu sucesso; falta o /dock_status confirmar, dentro do prazo.
    if entrada.na_base:
        p.evento('dock_ok')
        motivo = p.estado.motivo_doca
        p.mudar(fase=CARREGANDO, tentativas_dock=0, t_resultado_dock=None)
        if motivo == POR_FALHAS:
            # PAT-08: encerra depois do dock confirmado.
            return p.encerrar(CODIGO_FALHAS, 'falhas_seguidas')
        return p.saida()
    if entrada.agora - p.estado.t_resultado_dock > cfg.tempos.confirma_dock_s:
        return _dock_nao_confirmado(p, entrada, cfg, 'sem_is_docked', None)
    return p.saida()


def _dock_nao_confirmado(p, entrada, cfg, detalhe, codigo):
    """PAT-10 e PAT-11: tenta de novo, até o limite de tentativas."""
    p.evento('dock_nao_confirmado', detalhe=detalhe, resultado=codigo)
    p.mudar(t_resultado_dock=None)
    if p.estado.tentativas_dock >= cfg.tentativas_dock:
        return p.encerrar(CODIGO_DOCK, 'dock_falhou')
    p.evento('destino_enviado', detalhe=f'aproximacao_doca:{p.estado.motivo_doca}')
    p.enviar(entrada.agora, APROXIMACAO)
    p.mudar(fase=INDO_DOCA)
    return p.saida()

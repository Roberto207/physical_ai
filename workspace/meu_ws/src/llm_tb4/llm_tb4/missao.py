"""O que fazer com cada pedido e com cada resposta do robô. Sem ROS: toda a regra está aqui.

Mesmo desenho do patrulha_tb4/decisao.py: `decidir(estado, evento, sensores, agora, cfg)`
devolve o estado novo e a lista de ações; quem fala com o ROS (execucao.py) só as executa.

Regras do operador (specs/llm-integracao/PLANO.md):
- sem aprovação por ação;
- mensagem durante o trajeto cancela a meta na chegada e vira a ordem principal;
- durante o dock e a saída da doca a manobra termina e a última mensagem é obedecida;
- "parar" cancela qualquer coisa, na hora;
- parado e interpretando, as outras mensagens são ignoradas.

Ações devolvidas (tuplas):
    ('interpretar', epoca, frase)   consultar o modelo
    ('enviar', seq, Passo)          mandar uma meta
    ('cancelar', seq)               cancelar a meta nossa
    ('cancelar_tudo',)              cancelar qualquer meta de navegação
    ('log', nivel, texto)
"""
from dataclasses import dataclass, replace
from typing import Callable, Optional

PARADO, PREPARANDO, ENVIANDO, EXECUTANDO, CONFIRMANDO, CANCELANDO, TRAVADO = (
    'parado', 'preparando', 'enviando', 'executando', 'confirmando', 'cancelando', 'travado')
SAIR, NAVEGAR, ENCAIXAR = 'sair', 'navegar', 'encaixar'

PRAZO_PREPARO_S = 20      # esperar sensores e servidores ficarem prontos (ex.: lidar após sair)
PRAZO_ACEITE_S = 10
PRAZO_NAVEGAR_S = 120     # o mesmo TEMPO_DESTINO_S da patrulha oficial
PRAZO_MANOBRA_S = 60
PRAZO_CONFIRMAR_S = 20
PRAZO_CANCELAR_S = 5
VALIDADE_INTERPRETACAO_S = 10

IDADE_DOCA_S = 15
IDADE_BATERIA_S = 30      # o robô publica a bateria a cada 5 s
IDADE_TF_S = 2
IDADE_TF_PERDIDA_S = 10   # durante o trajeto: sem localização, cancela
IDADE_DOCA_PERDIDA_S = 30
BATERIA_MINIMA = 0.20


@dataclass(frozen=True)
class Passo:
    tipo: str
    nome: str
    x: float = 0.0
    y: float = 0.0
    graus: float = 0.0
    exige_bateria: bool = False


@dataclass(frozen=True)
class Sensores:
    """Retrato das leituras. Idades em segundos; None quer dizer "nunca recebido"."""
    na_doca: Optional[bool] = None
    doca_visivel: bool = False
    idade_doca: Optional[float] = None
    bateria: Optional[float] = None
    idade_bateria: Optional[float] = None
    idade_tf: Optional[float] = None
    prontos: frozenset = frozenset()   # tipos de passo com servidor de ação disponível
    meta_alheia: bool = False


@dataclass(frozen=True)
class Config:
    freio: bool
    destino: Callable        # ação validada -> Passo de navegação
    aproximacao: Passo       # onde parar antes de encaixar


# ---- eventos
@dataclass(frozen=True)
class Mensagem:
    frase: str
    parar: bool


@dataclass(frozen=True)
class Ordem:
    """Resposta do interpretador. `acao` é None quando o pedido foi recusado."""
    epoca: int
    frase: str
    acao: Optional[dict] = None


@dataclass(frozen=True)
class Aceite:
    seq: int
    aceito: bool


@dataclass(frozen=True)
class Fim:
    seq: int
    sucesso: bool


@dataclass(frozen=True)
class Relogio:
    pass


@dataclass(frozen=True)
class Encerrar:
    pass


@dataclass
class Estado:
    fase: str = PARADO
    passos: tuple = ()
    seq: int = 0
    prazo: float = 0.0
    epoca: int = 0
    interpretando: Optional[tuple] = None    # (epoca, instante do pedido)
    substituindo: bool = False   # a interpretação em curso veio de quem interrompeu um movimento
    pendente: Optional[dict] = None          # ordem à espera do fim de manobra ou cancelamento
    problema: str = ''
    avisou_bateria: bool = False


def inicial(agora):
    """Começa ocupado com o aquecimento do modelo (época 0)."""
    return Estado(interpretando=(0, agora))


def aceita_mensagem(estado):
    """Falso só quando está parado interpretando um pedido (ou aquecendo o modelo)."""
    return not (estado.fase == PARADO and estado.interpretando and not estado.substituindo)


def bateria_ok(sensores):
    b = sensores.bateria
    return (b is not None and b == b and 0 <= b <= 1       # b == b descarta NaN
            and sensores.idade_bateria is not None
            and sensores.idade_bateria <= IDADE_BATERIA_S)


def impedimento(passo, sensores):
    """Por que este passo não pode ser enviado agora, ou None."""
    s = sensores
    if s.na_doca is None or s.idade_doca is None or s.idade_doca > IDADE_DOCA_S:
        return 'sem estado recente da doca'
    if passo.exige_bateria:
        if not bateria_ok(s):
            return 'sem leitura recente da bateria'
        if s.bateria < BATERIA_MINIMA:
            return 'bateria abaixo de 20%'
    if passo.tipo == SAIR and s.idade_tf is None:
        return 'localização nunca recebida (faça o 2D Pose Estimate)'
    if passo.tipo == NAVEGAR:
        if s.na_doca:
            return 'o robô ainda consta na doca'
        if s.idade_tf is None or s.idade_tf > IDADE_TF_S:
            return 'sem map→odom recente (faça o 2D Pose Estimate)'
    if passo.tipo == ENCAIXAR and not s.doca_visivel:
        return 'a doca não está visível'
    if passo.tipo not in s.prontos:
        return 'servidor de ação indisponível'
    if s.meta_alheia:
        return 'há uma meta ativa de outro programa'
    return None


def planejar(acao, sensores, cfg):
    """(passos, motivo da recusa). Passos vazios e sem motivo: não há nada a fazer."""
    if sensores.na_doca is None:
        return (), 'estado da doca desconhecido'
    nome, na_doca = acao['acao'], sensores.na_doca
    sair = Passo(SAIR, 'sair da doca', exige_bateria=True)
    encaixar = Passo(ENCAIXAR, 'encaixar na doca')
    if nome in ('ir_para', 'ir_para_coordenadas'):
        destino = cfg.destino(acao)
        return ((sair, destino) if na_doca else (destino,)), None
    if nome == 'voltar_para_base':
        return (() if na_doca else (cfg.aproximacao, encaixar)), None
    if nome == 'encaixar':
        return (() if na_doca else (encaixar,)), None
    if nome == 'sair_da_base':
        return ((sair,) if na_doca else ()), None
    return (), f'ação sem execução: {nome}'


class _Decisao:
    def __init__(self, estado, sensores, agora, cfg):
        self.e = replace(estado)
        self.s = sensores
        self.agora = agora
        self.cfg = cfg
        self.acoes = []

    def log(self, nivel, texto):
        self.acoes.append(('log', nivel, texto))

    # ------------------------------------------------------------ transições
    def parado(self):
        """Chega ao repouso e, se houver ordem guardada e nada mais novo, começa."""
        self.e.fase, self.e.passos = PARADO, ()
        if self.e.pendente is not None and self.e.interpretando is None:
            self.iniciar()

    def iniciar(self):
        acao, self.e.pendente = self.e.pendente, None
        passos, motivo = planejar(acao, self.s, self.cfg)
        if motivo:
            self.log('warn', f'NAO EXECUTADO: {motivo}')
        elif not passos:
            self.log('info', f'nada a fazer para {acao["acao"]}: o robô já está assim')
        else:
            self.e.passos = passos
            self.preparar()

    def preparar(self):
        self.e.fase, self.e.prazo = PREPARANDO, self.agora + PRAZO_PREPARO_S
        self.e.problema = ''
        self.tentar_enviar()

    def tentar_enviar(self):
        passo = self.e.passos[0]
        problema = impedimento(passo, self.s)
        if problema is None:
            self.e.seq += 1
            self.e.fase, self.e.prazo = ENVIANDO, self.agora + PRAZO_ACEITE_S
            self.e.avisou_bateria = False
            self.acoes.append(('enviar', self.e.seq, passo))
            self.log('info', f'EXECUTANDO: {passo.nome}')
        elif self.agora >= self.e.prazo:
            self.log('warn', f'NAO EXECUTADO: {passo.nome}: {problema}')
            self.parado()
        elif problema != self.e.problema:
            self.e.problema = problema
            self.log('info', f'aguardando para {passo.nome}: {problema}')

    def cancelar(self):
        self.acoes.append(('cancelar', self.e.seq))
        self.e.fase, self.e.prazo = CANCELANDO, self.agora + PRAZO_CANCELAR_S
        self.e.passos = self.e.passos[:1]

    def interromper(self, inclusive_manobra):
        fase = self.e.fase
        if fase == PREPARANDO:
            self.e.fase, self.e.passos = PARADO, ()
        elif fase == CONFIRMANDO:
            if inclusive_manobra:
                self.e.fase, self.e.passos = PARADO, ()
            else:
                self.e.passos = self.e.passos[:1]
        elif fase in (ENVIANDO, EXECUTANDO):
            if inclusive_manobra or self.e.passos[0].tipo == NAVEGAR:
                self.cancelar()
            else:   # a manobra termina; o resto da missão é descartado
                self.e.passos = self.e.passos[:1]
        elif fase == TRAVADO and inclusive_manobra:
            self.cancelar()

    def parar(self):
        self.e.epoca += 1
        self.e.interpretando, self.e.pendente, self.e.substituindo = None, None, False
        self.interromper(inclusive_manobra=True)
        if not self.cfg.freio:
            self.acoes.append(('cancelar_tudo',))

    def concluir_passo(self):
        self.e.passos = self.e.passos[1:]
        if self.e.passos:
            self.preparar()
        else:
            self.log('info', 'CONCLUIDO')
            self.parado()

    # ------------------------------------------------------------ eventos
    def mensagem(self, evento):
        if evento.parar:
            self.parar()
            return
        if not aceita_mensagem(self.e):
            self.log('warn', f'OCUPADO: pedido ignorado: {evento.frase!r}')
            return
        self.e.epoca += 1
        self.e.interpretando, self.e.pendente = (self.e.epoca, self.agora), None
        if self.e.fase != PARADO:
            self.e.substituindo = True
            self.interromper(inclusive_manobra=False)
        self.acoes.append(('interpretar', self.e.epoca, evento.frase))

    def ordem(self, evento):
        em_curso = self.e.interpretando
        if em_curso is None or evento.epoca != em_curso[0]:
            if evento.epoca:
                self.log('warn', f'DESCARTADO: {evento.frase!r} (chegou outra mensagem ou um '
                                 'pedido de parar)')
            return
        self.e.interpretando, self.e.substituindo = None, False
        if evento.acao is None:
            return
        if evento.acao['acao'] == 'parar':
            self.parar()
            return
        if self.agora - em_curso[1] > VALIDADE_INTERPRETACAO_S:
            self.log('warn', f'NAO EXECUTADO: a interpretação de {evento.frase!r} demorou mais '
                             f'de {VALIDADE_INTERPRETACAO_S} s')
        elif self.cfg.freio:
            return
        elif self.e.fase == TRAVADO:
            self.log('error', 'NAO EXECUTADO: um cancelamento não foi confirmado. Confira o '
                              'robô; "pare" repete o cancelamento.')
        else:
            self.e.pendente = evento.acao
            if self.e.fase == PARADO:
                self.iniciar()
            else:
                self.log('info', f'ordem guardada até terminar: {self.e.passos[0].nome}')

    def aceite(self, evento):
        fase = self.e.fase
        if evento.seq != self.e.seq or fase not in (ENVIANDO, CANCELANDO, TRAVADO):
            if evento.aceito:   # meta antiga aceita com atraso: não pode ficar andando
                self.acoes.append(('cancelar', evento.seq))
        elif not evento.aceito:
            self.log('warn', f'meta recusada: {self.e.passos[0].nome}')
            self.parado()
        elif fase == ENVIANDO:
            manobra = self.e.passos[0].tipo != NAVEGAR
            self.e.fase = EXECUTANDO
            self.e.prazo = self.agora + (PRAZO_MANOBRA_S if manobra else PRAZO_NAVEGAR_S)
        else:                   # aceite depois do pedido de cancelamento
            self.cancelar()

    def fim(self, evento):
        if evento.seq != self.e.seq:
            return
        fase = self.e.fase
        if fase in (CANCELANDO, TRAVADO):
            self.log('info', f'meta encerrada: {self.e.passos[0].nome}')
            self.parado()
        elif fase in (ENVIANDO, EXECUTANDO):
            passo = self.e.passos[0]
            if not evento.sucesso:
                self.log('warn', f'FALHOU: {passo.nome}. Missão interrompida.')
                self.parado()
            elif passo.tipo == NAVEGAR:
                self.concluir_passo()
            else:
                self.e.fase, self.e.prazo = CONFIRMANDO, self.agora + PRAZO_CONFIRMAR_S

    def desistir(self, motivo):
        self.log('warn', f'CANCELANDO: {motivo}')
        self.e.pendente = None
        self.cancelar()

    def relogio(self):
        fase, vencido = self.e.fase, self.agora >= self.e.prazo
        if fase == PREPARANDO:
            self.tentar_enviar()
        elif fase == ENVIANDO and vencido:
            self.log('error', 'sem resposta de aceite; movimento travado até confirmar')
            self.e.pendente = None
            self.acoes += [('cancelar', self.e.seq), ('cancelar_tudo',)]
            self.e.fase, self.e.passos = TRAVADO, self.e.passos[:1]
        elif fase == EXECUTANDO:
            passo, s = self.e.passos[0], self.s
            if vencido:
                self.desistir(f'{passo.nome} passou do prazo')
            elif passo.tipo == NAVEGAR:
                if s.idade_tf is None or s.idade_tf > IDADE_TF_PERDIDA_S:
                    self.desistir('localização (map→odom) parou de chegar')
                elif s.idade_doca is None or s.idade_doca > IDADE_DOCA_PERDIDA_S:
                    self.desistir('o estado da doca parou de chegar')
                elif (bateria_ok(s) and s.bateria < BATERIA_MINIMA
                      and not self.e.avisou_bateria):
                    self.e.avisou_bateria = True
                    self.log('warn', f'BATERIA BAIXA ({s.bateria:.0%}): peça "volte para a doca"')
        elif fase == CONFIRMANDO:
            esperado = self.e.passos[0].tipo == ENCAIXAR
            if self.s.na_doca is esperado:
                self.concluir_passo()
            elif vencido:
                self.log('error', f'doca não confirmada após {self.e.passos[0].nome}')
                self.e.pendente = None
                self.parado()
        elif fase == CANCELANDO and vencido:
            self.log('error', 'o cancelamento não foi confirmado; confira o robô')
            self.e.fase, self.e.pendente = TRAVADO, None

    def encerrar(self):
        self.e.epoca += 1
        self.e.interpretando, self.e.pendente, self.e.substituindo = None, None, False
        ativo = self.e.fase != PARADO
        self.interromper(inclusive_manobra=True)
        if ativo and not self.cfg.freio:
            self.acoes.append(('cancelar_tudo',))


def decidir(estado, evento, sensores, agora, cfg):
    d = _Decisao(estado, sensores, agora, cfg)
    if isinstance(evento, Mensagem):
        d.mensagem(evento)
    elif isinstance(evento, Ordem):
        d.ordem(evento)
    elif isinstance(evento, Aceite):
        d.aceite(evento)
    elif isinstance(evento, Fim):
        d.fim(evento)
    elif isinstance(evento, Relogio):
        d.relogio()
    elif isinstance(evento, Encerrar):
        d.encerrar()
    else:
        raise ValueError(f'evento desconhecido: {evento!r}')
    return d.e, d.acoes

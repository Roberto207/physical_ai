"""Ponte entre a missao.py e o robô: lê os sensores e envia ou cancela metas.

Usa o TurtleBot4Navigator oficial (turtlebot4_navigation) pelos clientes de ação e pelo
getPoseStamped, sempre de forma assíncrona. Os atalhos prontos (startToPose, goToPose,
cancelTask, dock, undock) não são usados: esperam sem prazo, o que deixaria o "pare" sem
resposta, e numa recusa conservam o resultado da meta anterior (padrão do no_patrulha.py).
Nada aqui bloqueia: tudo roda no executor do nó.
"""
import time

from action_msgs.msg import GoalStatus, GoalStatusArray
from action_msgs.srv import CancelGoal
from irobot_create_msgs.action import Dock, Undock
from irobot_create_msgs.msg import DockStatus
from nav2_msgs.action import NavigateToPose
from rclpy.qos import (DurabilityPolicy, QoSProfile, ReliabilityPolicy,
                       qos_profile_sensor_data)
from sensor_msgs.msg import BatteryState
from tf2_msgs.msg import TFMessage

from llm_tb4.missao import ENCAIXAR, NAVEGAR, SAIR, Aceite, Fim, Sensores

ACOES = ('navigate_to_pose', 'dock', 'undock')
ATIVOS = (GoalStatus.STATUS_ACCEPTED, GoalStatus.STATUS_EXECUTING, GoalStatus.STATUS_CANCELING)


class Robo:
    def __init__(self, no, navegador, avisar):
        """`avisar(evento)` entrega Aceite e Fim para a missão."""
        self.no, self.nav, self.avisar = no, navegador, avisar
        self.na_doca = None
        self.doca_visivel = False
        self.bateria = None
        self.quando = {}              # 'doca', 'bateria', 'tf' -> instante da última leitura
        self.metas = {}               # seq -> goal handle
        self.cancelar_ao_aceitar = set()
        self.minhas = set()           # ids das nossas metas
        self.ativas = {}              # ação -> ids de metas ativas no servidor
        self.clientes = {NAVEGAR: navegador.nav_to_pose_client,
                         SAIR: navegador.undock_action_client,
                         ENCAIXAR: navegador.dock_action_client}

        no.create_subscription(DockStatus, 'dock_status', self._doca, qos_profile_sensor_data)
        no.create_subscription(BatteryState, 'battery_state', self._bateria,
                               qos_profile_sensor_data)
        no.create_subscription(TFMessage, 'tf', self._tf,
                               QoSProfile(depth=100, reliability=ReliabilityPolicy.BEST_EFFORT))
        estado = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                            durability=DurabilityPolicy.TRANSIENT_LOCAL)
        for acao in ACOES:
            no.create_subscription(
                GoalStatusArray, f'{acao}/_action/status',
                lambda m, acao=acao: self._status(acao, m), estado)
        self.cancelar_navegacao = no.create_client(CancelGoal,
                                                   'navigate_to_pose/_action/cancel_goal')

    # ------------------------------------------------------------ sensores
    def _doca(self, mensagem):
        self.na_doca, self.doca_visivel = mensagem.is_docked, mensagem.dock_visible
        self.quando['doca'] = time.monotonic()

    def _bateria(self, mensagem):
        self.bateria = mensagem.percentage
        self.quando['bateria'] = time.monotonic()

    def _tf(self, mensagem):
        # Conta a chegada, e não o carimbo: os relógios do robô e do PC podem divergir.
        if any((t.header.frame_id.lstrip('/'), t.child_frame_id.lstrip('/')) == ('map', 'odom')
               for t in mensagem.transforms):
            self.quando['tf'] = time.monotonic()

    def _status(self, acao, mensagem):
        self.ativas[acao] = {bytes(s.goal_info.goal_id.uuid)
                             for s in mensagem.status_list if s.status in ATIVOS}

    def sensores(self):
        agora = time.monotonic()

        def idade(nome):
            return agora - self.quando[nome] if nome in self.quando else None

        return Sensores(
            na_doca=self.na_doca, doca_visivel=self.doca_visivel, idade_doca=idade('doca'),
            bateria=self.bateria, idade_bateria=idade('bateria'), idade_tf=idade('tf'),
            prontos=frozenset(t for t, c in self.clientes.items() if c.server_is_ready()),
            meta_alheia=any(ids - self.minhas for ids in self.ativas.values()))

    # ------------------------------------------------------------ metas
    def _meta(self, passo):
        if passo.tipo == NAVEGAR:
            meta = NavigateToPose.Goal()
            meta.pose = self.nav.getPoseStamped([passo.x, passo.y], passo.graus)
            return meta
        return Undock.Goal() if passo.tipo == SAIR else Dock.Goal()

    def enviar(self, seq, passo):
        try:
            futuro = self.clientes[passo.tipo].send_goal_async(self._meta(passo))
        except Exception as erro:
            self.no.get_logger().error(f'não consegui enviar {passo.nome}: {erro!r}')
            self.avisar(Aceite(seq, False))
            return
        futuro.add_done_callback(lambda f: self._aceitou(seq, f))

    def _aceitou(self, seq, futuro):
        meta = None if futuro.exception() else futuro.result()
        if meta is None or not meta.accepted:
            self.avisar(Aceite(seq, False))
            return
        self.metas[seq] = meta
        self.minhas.add(bytes(meta.goal_id.uuid))
        if seq in self.cancelar_ao_aceitar:
            meta.cancel_goal_async()
        resultado = meta.get_result_async()
        self.avisar(Aceite(seq, True))
        resultado.add_done_callback(lambda f: self._terminou(seq, f))

    def _terminou(self, seq, futuro):
        sucesso = (not futuro.exception() and futuro.result() is not None
                   and futuro.result().status == GoalStatus.STATUS_SUCCEEDED)
        self.metas.pop(seq, None)
        self.avisar(Fim(seq, sucesso))

    def cancelar(self, seq):
        """Cancela a nossa meta; se ela ainda não foi aceita, cancela assim que for."""
        if seq in self.metas:
            self.metas[seq].cancel_goal_async()
        else:
            self.cancelar_ao_aceitar.add(seq)

    def cancelar_tudo(self):
        """Cancela qualquer meta de navegação, inclusive de outro programa ou órfã: o pedido
        com identificador e horário zerados vale para todas (action_msgs/srv/CancelGoal)."""
        if self.cancelar_navegacao.service_is_ready():
            self.cancelar_navegacao.call_async(CancelGoal.Request())

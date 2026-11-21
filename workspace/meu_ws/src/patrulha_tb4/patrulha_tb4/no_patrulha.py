"""O nó da patrulha: lê os sensores, chama `decidir()` e executa (PAT, AMB e OBS).

Toda a decisão está em `decisao.py`. Aqui só há a ponte com o ROS:

- um nó monitor, numa thread, que guarda a última bateria, o último `/dock_status` e o
  instante da última mensagem de `/clock` (o mesmo padrão do `BatteryMonitor` do
  `patrol_loop.py` oficial);
- o `TurtleBot4Navigator` oficial, usado sem alterações, para o Nav2, o dock e o undock.

O nó não sabe quem responde do outro lado (base falsa, Create 3 simulada ou robô real).
"""
import math
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from geometry_msgs.msg import PoseStamped
from irobot_create_msgs.action import Dock, Undock
from irobot_create_msgs.msg import DockStatus
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import BatteryState
from std_srvs.srv import Trigger
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator

from patrulha_tb4 import __version__, decisao
from patrulha_tb4.config import ConfigInvalida, hash_arquivo
from patrulha_tb4.pontos import validar_configuracao
from patrulha_tb4.registro import Registro, hash_codigo

ESPERA_CANCELAMENTO_S = 1.0  # tempo de relógio; cabe no prazo do PAT-15


class Monitor(Node):
    """Guarda as últimas leituras. Roda numa thread própria, para nunca ficar para trás."""

    def __init__(self, acordar, ao_pedir_doca):
        super().__init__('patrulha_monitor')
        self._acordar = acordar
        self._ao_pedir_doca = ao_pedir_doca
        self._trava = threading.Lock()
        self._bateria = None
        self._t_bateria = None
        self._na_base = None
        self._parede_relogio = None
        self.usa_sim_time = self.get_parameter('use_sim_time').value
        self.create_subscription(BatteryState, 'battery_state', self._ao_receber_bateria,
                                 qos_profile_sensor_data)
        self.create_subscription(DockStatus, 'dock_status', self._ao_receber_doca,
                                 qos_profile_sensor_data)
        self.create_subscription(
            Clock, '/clock', self._ao_receber_relogio,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
        # PAT-23e: o nome é relativo, então vale no namespace do nó (/robot1/patrulha/voltar_doca).
        # O serviço roda na thread do monitor: responde mesmo com o laço de decisão ocupado.
        self.create_service(Trigger, 'patrulha/voltar_doca', self._ao_pedir_retorno)

    def agora(self):
        """Relógio do ROS em segundos. None enquanto o tempo simulado não chegou."""
        with self._trava:
            sem_relogio = self.usa_sim_time and self._parede_relogio is None
        if sem_relogio:
            return None
        return self.get_clock().now().nanoseconds / 1e9

    def leitura(self):
        with self._trava:
            return self._bateria, self._t_bateria, self._na_base, self._parede_relogio

    def _ao_receber_bateria(self, mensagem):
        agora = self.agora()
        with self._trava:
            self._bateria = mensagem.percentage
            self._t_bateria = agora
        self._acordar.set()  # a decisão roda logo depois de cada bateria (PAT-06)

    def _ao_receber_doca(self, mensagem):
        with self._trava:
            self._na_base = mensagem.is_docked

    def _ao_receber_relogio(self, _mensagem):
        with self._trava:
            self._parede_relogio = time.time()

    def _ao_pedir_retorno(self, _pedido, resposta):
        """PAT-23e: só registra o pedido e acorda o laço. Quem decide é a `decidir()`."""
        self._ao_pedir_doca()
        self.get_logger().info('Pedido de retorno à doca recebido.')
        resposta.success = True
        resposta.message = 'pedido registrado'
        return resposta


class Patrulha:
    """Executa as ações que `decidir()` pede e devolve os resultados."""

    def __init__(self, caminho_config, ambiente_pedido, pasta_log):
        self._acordar = threading.Event()
        self._sinal = threading.Event()
        self._pedido_doca = threading.Event()   # PAT-23: nível, nunca limpo
        self.monitor = Monitor(self._acordar, self._pedir_doca)
        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self.monitor)
        threading.Thread(target=self._executor.spin, daemon=True).start()

        self.caminho_config = caminho_config
        self.ambiente_pedido = ambiente_pedido
        arquivo = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.jsonl'
        self.registro = Registro(os.path.join(pasta_log, arquivo))
        self.estado = decisao.Estado()
        self.cfg = None
        self.nav = None
        self._ativa = None            # ação em andamento, do ponto de vista do nó
        self._futuro_base = None      # futuro do resultado do dock ou do undock
        self._futuro_envio = None     # resposta de aceitação do dock ou do undock
        self._meta_base = None        # goal handle do dock ou do undock
        self._rejeitada = None        # resultado pronto, quando o servidor recusa o pedido
        self._nav2_pronto = threading.Event()

    # ------------------------------------------------------------ início e fim

    def _pedir_doca(self):
        self._pedido_doca.set()
        self._acordar.set()   # a decisão roda já: o PAT-23 pede reação em até 2 s

    def tratar_sinal(self, _numero, _quadro):
        self._sinal.set()
        self._acordar.set()

    def rodar(self):
        codigo = self._iniciar()
        if codigo is None:
            codigo = self._laco()
        return codigo

    def _iniciar(self):
        """OBS-03 e VAL: grava o início e confere a configuração antes de qualquer ação."""
        try:
            hash_config = hash_arquivo(self.caminho_config)
        except OSError:
            hash_config = None
        try:
            config, problemas = validar_configuracao(self.caminho_config)
            erro = None
        except ConfigInvalida as falha:
            config, problemas, erro = None, [], falha

        self.registro.gravar(
            'inicio', decisao.INICIANDO, None, self.monitor.agora(),
            versao=__version__, hash_codigo=_hash_do_pacote(), hash_config=hash_config or '',
            ambiente=config.ambiente if config else (self.ambiente_pedido or 'desconhecido'),
            modelo=config.modelo if config else 'desconhecido')
        self.monitor.get_logger().info(f'Log da patrulha: {self.registro.caminho}')

        if erro is not None:
            return self._config_invalida(erro.motivo, erro.detalhe)
        if problemas:
            for nome, motivo in problemas:
                self._gravar('config_invalida', detalhe=f'{nome}: {motivo}')
            return self._sair(decisao.CODIGO_CONFIG)
        if self.ambiente_pedido and self.ambiente_pedido != config.ambiente:
            return self._config_invalida(
                'ambiente_diverge', f'launch={self.ambiente_pedido} config={config.ambiente}')
        if self.monitor.usa_sim_time != config.usa_tempo_simulado:  # AMB-02
            return self._config_invalida(
                'use_sim_time_diverge',
                f'use_sim_time={self.monitor.usa_sim_time} ambiente={config.ambiente}')

        self.cfg = config
        # O navegador é outro nó e recebe o mesmo __ns do launch (ex.: /robot1).
        # No Humble, TurtleBot4Navigator.__init__ não aceita o argumento namespace;
        # o remapeamento global do ROS aplica o namespace também a este nó.
        self.nav = TurtleBot4Navigator()
        threading.Thread(target=self._esperar_nav2, daemon=True).start()
        return None

    def _esperar_nav2(self):
        """Informa a pose inicial e espera o Nav2 ativar. Não é ação de movimento."""
        try:
            self.nav.setInitialPose(self._pose_ros(self.cfg.pose_inicial))
            self.nav.waitUntilNav2Active()
            self._nav2_pronto.set()
            self._acordar.set()
        except Exception as erro:  # o processo está encerrando
            self.monitor.get_logger().debug(f'espera do Nav2 interrompida: {erro}')

    def _config_invalida(self, motivo, detalhe=''):
        self._gravar('config_invalida', detalhe=f'{motivo}: {detalhe}' if detalhe else motivo)
        return self._sair(decisao.CODIGO_CONFIG)

    def _sair(self, codigo):
        """OBS-02: o resumo sai em qualquer encerramento com código."""
        bateria = self.monitor.leitura()[0]
        self.registro.gravar_resumo(decisao.ENCERRANDO, bateria, self.monitor.agora(),
                                    voltas=self.estado.voltas, codigo_saida=codigo)
        self.registro.fechar()
        self.monitor.get_logger().info(f'Patrulha encerrada com o código {codigo}.')
        return codigo

    # ------------------------------------------------------------ laço

    def _laco(self):
        while True:
            self._acordar.clear()
            bateria, t_bateria, na_base, parede_relogio = self.monitor.leitura()
            self.registro.observar_bateria(bateria)
            entrada = decisao.Entrada(
                parede=time.time(), agora=self.monitor.agora(), bateria=bateria,
                t_bateria=t_bateria, na_base=na_base, servidores_ok=self._servidores_ok(),
                resultado=self._colher_resultado(), sinal=self._sinal.is_set(),
                usa_sim_time=self.monitor.usa_sim_time, parede_relogio=parede_relogio,
                pedido_doca=self._pedido_doca.is_set())
            saida = decisao.decidir(self.estado, entrada, self.cfg)
            self.estado = saida.estado
            # O destino_enviado só é gravado depois que o pedido saiu de fato: assim o
            # t_parede dele mede o tempo de reação (PAT-06). O resto é gravado antes.
            enviados = [e for e in saida.eventos if e['evento'] == 'destino_enviado']
            for evento in saida.eventos:
                if evento['evento'] != 'destino_enviado':
                    self._gravar(**evento)
            codigo = None
            for acao in saida.acoes:
                if acao[0] == decisao.ENCERRAR:
                    codigo = acao[1]
                else:
                    self._executar(acao)
            for evento in enviados:
                self._gravar(**evento)
            if codigo is not None:
                return self._sair(codigo)
            self._acordar.wait(decisao.PERIODO_S)

    def _gravar(self, evento, **campos):
        bateria = self.monitor.leitura()[0]
        self.registro.gravar(evento, self.estado.fase, bateria, self.monitor.agora(), **campos)
        texto = ' '.join(f'{campo}={valor}' for campo, valor in campos.items())
        self.monitor.get_logger().info(f'[{self.estado.fase}] {evento} {texto}'.rstrip())

    def _servidores_ok(self):
        """PAT-20: Nav2 ativo e os servidores de dock e undock respondendo."""
        if not self._nav2_pronto.is_set():
            return False
        return (self.nav.nav_to_pose_client.server_is_ready()
                and self.nav.dock_action_client.server_is_ready()
                and self.nav.undock_action_client.server_is_ready())

    # ------------------------------------------------------------ ações

    def _pose_ros(self, pose):
        """O único lugar que monta uma pose do ROS: sempre a partir da configuração."""
        mensagem = PoseStamped()
        mensagem.header.frame_id = 'map'
        mensagem.header.stamp = self.nav.get_clock().now().to_msg()
        mensagem.pose.position.x = pose.x
        mensagem.pose.position.y = pose.y
        meio = math.radians(pose.yaw_graus) / 2
        mensagem.pose.orientation.z = math.sin(meio)
        mensagem.pose.orientation.w = math.cos(meio)
        return mensagem

    def _executar(self, acao):
        nome = acao[0]
        if nome == decisao.CANCELAR:
            self._cancelar()
        elif nome == decisao.DESTINO:
            self._navegar(nome, self.cfg.pontos[acao[1]])
        elif nome == decisao.APROXIMACAO:
            self._navegar(nome, self.cfg.aproximacao_doca)
        elif nome == decisao.DOCK:
            self._enviar_base(nome, self.nav.dock_action_client, Dock.Goal())
        elif nome == decisao.UNDOCK:
            self._enviar_base(nome, self.nav.undock_action_client, Undock.Goal())
        else:
            raise ValueError(f'ação desconhecida: {nome}')

    def _navegar(self, nome, pose):
        self._ativa = nome
        if not self.nav.goToPose(self._pose_ros(pose)):
            self._rejeitada = decisao.Resultado(nome, decisao.FALHOU, 'rejeitado')

    def _enviar_base(self, nome, cliente, pedido):
        """Dock e undock sem travar o laço: envia e passa a consultar o resultado."""
        self._ativa = nome
        self._futuro_base = self._meta_base = self._futuro_envio = None
        try:
            self._futuro_envio = cliente.send_goal_async(pedido)
        except Exception as erro:
            self._rejeitada = decisao.Resultado(nome, decisao.FALHOU,
                                                 f'erro_envio:{erro}')

    def _colher_resultado(self):
        """Devolve o resultado da ação ativa, se ela terminou. Senão, None."""
        if self._ativa is None:
            return None
        nome = self._ativa
        if self._rejeitada is not None:
            resultado, self._rejeitada, self._ativa = self._rejeitada, None, None
            return resultado
        if nome in (decisao.DESTINO, decisao.APROXIMACAO):
            if not self.nav.isTaskComplete():
                return None
            codigo = self.nav.status
        else:
            if self._futuro_envio is not None:
                rclpy.spin_until_future_complete(self.nav, self._futuro_envio,
                                                 timeout_sec=0.1)
                if not self._futuro_envio.done():
                    return None
                try:
                    meta = self._futuro_envio.result()
                except Exception as erro:
                    self._futuro_envio = self._ativa = None
                    return decisao.Resultado(nome, decisao.FALHOU,
                                            f'erro_resposta:{erro}')
                self._futuro_envio = None
                if meta is None or not meta.accepted:
                    self._ativa = None
                    return decisao.Resultado(nome, decisao.FALHOU, 'rejeitado')
                self._meta_base = meta
                self._futuro_base = meta.get_result_async()
            rclpy.spin_until_future_complete(self.nav, self._futuro_base, timeout_sec=0.1)
            if not self._futuro_base.done() or self._futuro_base.result() is None:
                return None
            codigo = self._futuro_base.result().status
            self._futuro_base = self._meta_base = None
        self._ativa = None
        if codigo == GoalStatus.STATUS_SUCCEEDED:
            status = decisao.SUCESSO
        elif codigo == GoalStatus.STATUS_CANCELED:
            status = decisao.CANCELADO
        else:
            status = decisao.FALHOU
        return decisao.Resultado(nome, status, codigo)

    def _cancelar(self):
        """Cancela a ação ativa e espera ela terminar, por até ESPERA_CANCELAMENTO_S.

        A espera importa: um destino novo enviado enquanto o Nav2 ainda está cancelando
        o anterior é abortado por ele (visto no L1 de 2026-11-12).
        """
        nome, self._ativa, self._rejeitada = self._ativa, None, None
        if nome in (decisao.DESTINO, decisao.APROXIMACAO):
            meta, resultado = self.nav.goal_handle, self.nav.result_future
        else:
            meta, resultado = self._meta_base, self._futuro_base
            envio = self._futuro_envio
            self._futuro_base = self._meta_base = self._futuro_envio = None
            if meta is None and envio is not None:
                # Aguarda brevemente a confirmação para cancelar um pedido que acabou
                # de ser aceito. Se ela chegar depois, tenta cancelar no callback.
                def cancelar_se_aceito(futuro):
                    try:
                        confirmado = futuro.result()
                        if confirmado is not None and confirmado.accepted:
                            confirmado.cancel_goal_async()
                    except Exception:
                        pass
                if not envio.done():
                    rclpy.spin_until_future_complete(
                        self.nav, envio, timeout_sec=ESPERA_CANCELAMENTO_S)
                if envio.done():
                    cancelar_se_aceito(envio)
                else:
                    envio.add_done_callback(cancelar_se_aceito)
        if meta is None:
            return
        limite = time.monotonic() + ESPERA_CANCELAMENTO_S
        pedido = meta.cancel_goal_async()
        rclpy.spin_until_future_complete(self.nav, pedido, timeout_sec=ESPERA_CANCELAMENTO_S)
        restante = limite - time.monotonic()
        if resultado is not None and restante > 0:
            rclpy.spin_until_future_complete(self.nav, resultado, timeout_sec=restante)


def _hash_do_pacote():
    """OBS-03: hash dos .py do pacote e do launch, do jeito que estão instalados."""
    pacote = Path(__file__).resolve().parent
    try:
        launch = Path(get_package_share_directory('patrulha_tb4')) / 'launch'
    except PackageNotFoundError:
        launch = pacote.parent / 'launch'
    return hash_codigo([('patrulha_tb4', pacote), ('launch', launch.resolve())])


def main(args=None):
    # Sem o tratador de sinais do rclpy: o Ctrl+C precisa cancelar a ação antes de sair (PAT-15).
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    parametros = Node('patrulha_parametros')
    caminho = parametros.declare_parameter('config', '').value
    ambiente = parametros.declare_parameter('ambiente', '').value
    pasta_log = parametros.declare_parameter(
        'pasta_log', os.path.expanduser('~/.ros/patrulha')).value
    parametros.destroy_node()

    patrulha = Patrulha(caminho, ambiente, os.path.expanduser(pasta_log))
    signal.signal(signal.SIGINT, patrulha.tratar_sinal)
    signal.signal(signal.SIGTERM, patrulha.tratar_sinal)
    codigo = patrulha.rodar()
    sys.stdout.flush()
    sys.stderr.flush()
    # Saída direta: a thread que espera o Nav2 pode estar presa, e o código de saída é o que vale.
    os._exit(codigo)


if __name__ == '__main__':
    main()

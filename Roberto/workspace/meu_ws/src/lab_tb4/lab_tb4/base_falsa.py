#!/usr/bin/env python3
"""Finge as peças do TurtleBot 4 que o simulador leve (nav2_loopback_sim) não tem.

Só para treino sem Gazebo. Bateria e base aqui são INVENTADAS: servem para exercitar
a lógica da missão, não para medir nada sobre o robô real. Nada deste arquivo vai para o robô.

Rode com `ros2 run lab_tb4 base_falsa --ros-args -p battery_start:=0.9 ...` (até 2026-11-18,
era infra/tools/fake_tb4_base.py; os parâmetros e os padrões não mudaram, LCH-03).

O que este nó oferece:
- /battery_state: bateria que descarrega fora da base e carrega nela
- /dock_status e as actions /dock e /undock: base de carga falsa, que "encaixa" na hora
- /amcl/get_state e /amcl_pose: resposta de "localização ativa", pois o simulador leve
  já sabe a posição exata e não roda AMCL, mas waitUntilNav2Active() espera por ele

Parâmetros de sempre: battery_start, drain_per_s e charge_per_s (fração por segundo).

Parâmetros para provocar falhas de propósito (spec specs/patrol-inf, DESIGN seção 2).
Com os valores padrão, nada muda no comportamento:
- falhar_dock_n (0): o dock falha nas N primeiras vezes (TST-04)
- queda_bateria_em_s (-1) e queda_bateria_para (0.15): tantos segundos depois do primeiro
  undock, a bateria cai de uma vez para esse valor (TST-05)
- parar_bateria_em_s (-1): tantos segundos depois do primeiro undock, a bateria deixa de
  ser publicada (PAT-18 e PAT-18b)
- comecar_na_doca (true): false faz o robô "nascer" fora da doca (PAT-17)
- simular_bateria, simular_doca e simular_amcl (true): desligam cada parte. No Gazebo,
  servem para ligar só o que faltar (por exemplo, só a bateria)
"""
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from irobot_create_msgs.action import Dock, Undock
from irobot_create_msgs.msg import DockStatus
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import BatteryState


class FakeTb4Base(Node):

    def __init__(self):
        super().__init__('fake_tb4_base')
        self.percent = self.declare_parameter('battery_start', 0.5).value
        self.drain = self.declare_parameter('drain_per_s', 0.002).value
        self.charge = self.declare_parameter('charge_per_s', 0.05).value
        self.falhar_dock_n = self.declare_parameter('falhar_dock_n', 0).value
        self.queda_em_s = self.declare_parameter('queda_bateria_em_s', -1.0).value
        self.queda_para = self.declare_parameter('queda_bateria_para', 0.15).value
        self.parar_bateria_em_s = self.declare_parameter('parar_bateria_em_s', -1.0).value
        self.docked = self.declare_parameter('comecar_na_doca', True).value
        self.simular_bateria = self.declare_parameter('simular_bateria', True).value
        self.simular_doca = self.declare_parameter('simular_doca', True).value
        self.simular_amcl = self.declare_parameter('simular_amcl', True).value
        self.fora_ha_s = None  # segundos desde o primeiro undock
        self.queda_feita = False

        if self.simular_bateria:
            self.battery_pub = self.create_publisher(
                BatteryState, 'battery_state', qos_profile_sensor_data)
        if self.simular_doca:
            self.dock_pub = self.create_publisher(
                DockStatus, 'dock_status', qos_profile_sensor_data)
            ActionServer(self, Dock, 'dock', self.do_dock)
            ActionServer(self, Undock, 'undock', self.do_undock)
        if self.simular_amcl:
            self.pose_pub = self.create_publisher(
                PoseWithCovarianceStamped, 'amcl_pose',
                QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                           reliability=ReliabilityPolicy.RELIABLE))
            self.create_service(GetState, 'amcl/get_state', self.amcl_state)
        self.create_timer(1.0, self.tick)

    def tick(self):
        if self.fora_ha_s is not None:
            self.fora_ha_s += 1.0
        delta = self.charge if self.docked else -self.drain
        self.percent = min(1.0, max(0.0, self.percent + delta))
        if self._passou(self.queda_em_s) and not self.queda_feita:
            self.queda_feita = True
            self.percent = min(self.percent, self.queda_para)
            self.get_logger().info(f'falha provocada: bateria caiu para {self.percent:.0%}')
        if self.simular_bateria and not self._passou(self.parar_bateria_em_s):
            self.battery_pub.publish(BatteryState(percentage=self.percent))
        if self.simular_doca:
            self.publicar_doca()
        if self.simular_amcl:
            pose = PoseWithCovarianceStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            self.pose_pub.publish(pose)

    def _passou(self, limite_s):
        return limite_s >= 0 and self.fora_ha_s is not None and self.fora_ha_s >= limite_s

    def publicar_doca(self):
        self.dock_pub.publish(DockStatus(is_docked=self.docked, dock_visible=self.docked))

    def amcl_state(self, _request, response):
        response.current_state.id = State.PRIMARY_STATE_ACTIVE
        response.current_state.label = 'active'
        return response

    def do_dock(self, handle):
        if self.falhar_dock_n > 0:
            self.falhar_dock_n -= 1
            self.get_logger().info('falha provocada: dock falso NÃO encaixou')
            handle.abort()
            return Dock.Result(is_docked=False)
        self.docked = True
        # Publica na hora, sem esperar o próximo tick: quem checar o status logo depois
        # do dock precisa ver o valor novo (hipótese H2 da spec, PAT-09).
        self.publicar_doca()
        self.get_logger().info(f'dock falso: encaixado com {self.percent:.0%}')
        handle.succeed()
        return Dock.Result(is_docked=True)

    def do_undock(self, handle):
        self.docked = False
        if self.fora_ha_s is None:
            self.fora_ha_s = 0.0
        self.publicar_doca()
        self.get_logger().info(f'undock falso: saiu com {self.percent:.0%}')
        handle.succeed()
        return Undock.Result(is_docked=False)


def main():
    rclpy.init()
    node = FakeTb4Base()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

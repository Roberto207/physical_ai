"""Sobe só o nó da patrulha. Não abre o RViz (AMB-03).

Argumentos:
  config        arquivo YAML da patrulha (obrigatório)
  ambiente      leve, gazebo ou real. Se vier, precisa bater com o da configuração
  use_sim_time  true ou false. Se faltar, segue o ambiente da configuração (AMB-02)
  namespace     namespace do robô (ex.: /robot1). Vazio = sem namespace, como no simulador

O que roda ao lado do nó (Nav2, base falsa, Gazebo) não é deste pacote (AMB-01).
"""
import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _ambiente_da_config(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as arquivo:
            return yaml.safe_load(arquivo)['patrulha']['ambiente']
    except Exception:
        return None  # o nó grava config_invalida e sai com o código 2


def _montar(contexto):
    config = LaunchConfiguration('config').perform(contexto)
    ambiente = LaunchConfiguration('ambiente').perform(contexto)
    sim = LaunchConfiguration('use_sim_time').perform(contexto).strip().lower()
    if sim in ('true', 'false'):
        usa_sim_time = sim == 'true'
    else:
        usa_sim_time = (ambiente or _ambiente_da_config(config)) in ('leve', 'gazebo')

    # Os tópicos do nó são relativos (battery_state, dock_status): com o namespace eles viram
    # /robot1/battery_state etc. O nó passa o mesmo namespace ao TurtleBot4Navigator.
    no = Node(
        package='patrulha_tb4', executable='patrulha', output='screen',
        namespace=LaunchConfiguration('namespace').perform(contexto),
        parameters=[{'config': config, 'ambiente': ambiente, 'use_sim_time': usa_sim_time,
                     'pasta_log': LaunchConfiguration('pasta_log')}])
    # Quando a patrulha termina, o launch termina junto. O código de saída está no resumo do log.
    ao_sair = RegisterEventHandler(OnProcessExit(
        target_action=no, on_exit=[EmitEvent(event=Shutdown(reason='patrulha encerrada'))]))
    return [no, ao_sair]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('config', description='arquivo YAML da patrulha'),
        DeclareLaunchArgument('ambiente', default_value='',
                              description='leve, gazebo ou real (opcional)'),
        DeclareLaunchArgument('use_sim_time', default_value='',
                              description='true ou false (padrão: pelo ambiente)'),
        DeclareLaunchArgument('pasta_log', default_value='~/.ros/patrulha',
                              description='onde gravar o log JSONL'),
        DeclareLaunchArgument('namespace', default_value='',
                              description='namespace do robô, ex.: /robot1 (padrão: nenhum)'),
        OpaqueFunction(function=_montar),
    ])

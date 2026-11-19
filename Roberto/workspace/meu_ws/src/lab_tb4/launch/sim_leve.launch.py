"""Simulador leve do TurtleBot 4 no Humble: loopback + map_server + Nav2 + base falsa (SIM-03).

Argumentos:
  map           mapa YAML (obrigatório)
  nav2_perfil   bringup (nav2_params.yaml do nav2_bringup, o padrão do leve) ou turtlebot4
                (nav2.yaml do turtlebot4_navigation, usado no cenário l1b)
  rviz          true abre o RViz (SIM-03b). Padrão: false
  subir_base    true sobe a base falsa (padrão). false: só o simulador e o Nav2
  base          parâmetros da base falsa, em YAML de uma linha. Ex.: "{battery_start: 0.5}"

É o equivalente Humble do tb4_loopback_simulation.launch.py do nav2_bringup do Jazzy (ramo
jazzy, lido em 2026-11-18), que não existe no Humble. Mesmas peças, na mesma ordem:
- robot_state_publisher com o URDF do TurtleBot 4 (turtlebot4_description, modelo standard);
- TF estático base_footprint -> base_link (o loopback move o base_footprint);
- map_server + lifecycle_manager, com use_sim_time;
- o loopback (nav2_loopback_sim vendorizado em workspace/meu_ws/src/terceiros/), com os
  parâmetros que o nav2_params.yaml do Jazzy dava a ele (o do Humble não tem essa seção);
- a navegação do Nav2 (navigation_launch.py do Humble), com use_sim_time. Sem AMCL: o loopback
  já publica map -> odom. A base falsa responde ao amcl/get_state e ao amcl_pose, que o
  waitUntilNav2Active() do TurtleBot4Navigator espera.
O loopback publica o /clock (relógio de parede), e é por ele que o resto anda no "tempo simulado".

A base falsa sobe 15 s depois, como no script antigo: ela não depende do Nav2, mas assim os
logs ficam na mesma ordem das evidências antigas.
"""
import yaml
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            OpaqueFunction, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare

PERFIS_NAV2 = {
    'bringup': ('nav2_bringup', 'params', 'nav2_params.yaml'),
    'turtlebot4': ('turtlebot4_navigation', 'config', 'nav2.yaml'),
}

# Os valores da seção loopback_simulator do nav2_params.yaml do Jazzy, e o scan_frame_id que o
# tb4_loopback_simulation.launch.py passava (o lidar do TB4 é o rplidar_link).
PARAMETROS_LOOPBACK = {
    'base_frame_id': 'base_footprint',
    'odom_frame_id': 'odom',
    'map_frame_id': 'map',
    'scan_frame_id': 'rplidar_link',
    'update_duration': 0.02,
    'scan_range_min': 0.05,
    'scan_range_max': 30.0,
    'scan_angle_min': -3.1415,
    'scan_angle_max': 3.1415,
    'scan_angle_increment': 0.02617,
    'scan_use_inf': True,
}


def _share(pacote, *partes):
    return PathJoinSubstitution([FindPackageShare(pacote), *partes])


def _montar(contexto):
    perfil = LaunchConfiguration('nav2_perfil').perform(contexto)
    if perfil not in PERFIS_NAV2:
        raise RuntimeError(f'nav2_perfil inválido: {perfil} (use {", ".join(PERFIS_NAV2)})')
    params_nav2 = _share(*PERFIS_NAV2[perfil])
    base = yaml.safe_load(LaunchConfiguration('base').perform(contexto) or '{}') or {}

    robo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            _share('turtlebot4_description', 'launch', 'robot_description.launch.py')),
        launch_arguments={'model': 'standard', 'use_sim_time': 'true', 'namespace': ''}.items())

    pe_do_robo = Node(package='tf2_ros', executable='static_transform_publisher',
                      arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'base_link'])

    mapa = GroupAction([
        SetParameter('use_sim_time', True),
        Node(package='nav2_map_server', executable='map_server', name='map_server',
             output='screen', parameters=[{'yaml_filename': LaunchConfiguration('map')}]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_map_server', output='screen',
             parameters=[{'autostart': True, 'node_names': ['map_server']}]),
    ])

    loopback = Node(package='nav2_loopback_sim', executable='loopback_simulator',
                    name='loopback_simulator', output='screen',
                    parameters=[PARAMETROS_LOOPBACK])

    navegacao = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_share('nav2_bringup', 'launch', 'navigation_launch.py')),
        launch_arguments={'use_sim_time': 'true', 'params_file': params_nav2,
                          'autostart': 'true'}.items())

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_share('nav2_bringup', 'launch', 'rviz_launch.py')),
        launch_arguments={'use_sim_time': 'true'}.items(),
        condition=IfCondition(LaunchConfiguration('rviz')))

    base_falsa = TimerAction(period=15.0, actions=[
        Node(package='lab_tb4', executable='base_falsa', name='fake_tb4_base', output='screen',
             parameters=[base], condition=IfCondition(LaunchConfiguration('subir_base')))])

    return [robo, pe_do_robo, mapa, loopback, navegacao, rviz, base_falsa]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('map', description='mapa YAML'),
        DeclareLaunchArgument('nav2_perfil', default_value='bringup',
                              description='perfil do Nav2: bringup ou turtlebot4'),
        DeclareLaunchArgument('rviz', default_value='false', description='abre o RViz'),
        DeclareLaunchArgument('subir_base', default_value='true', description='sobe a base falsa'),
        DeclareLaunchArgument('base', default_value='{}',
                              description='parâmetros da base falsa, YAML de uma linha'),
        OpaqueFunction(function=_montar),
    ])

"""Nav2 oficial do TurtleBot 4 Humble com o timeout de bond do laboratório.

O nav2.launch.py do turtlebot4_navigation já põe o namespace e remapeia o scan dos costmaps
para <namespace>/scan. Falta só o bond_timeout: o padrão de 4 s derrubava os nós pelo Discovery
Server do lab ("after not receiving a heartbeat for 4000 ms"), e o gerente de ciclo de vida não
lê o params_file. O SetParameter entrega 120 s a todos os nós do grupo, gerente incluído.
Conferir no robô: ros2 param get <ns>/lifecycle_manager_navigation bond_timeout  → 120.0
"""
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetParameter


def generate_launch_description():
    oficial = get_package_share_directory('turtlebot4_navigation') + '/launch/nav2.launch.py'
    argumentos = ('namespace', 'params_file')
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('params_file'),
        GroupAction([
            SetParameter('bond_timeout', 120.0),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(oficial),
                launch_arguments={n: LaunchConfiguration(n) for n in argumentos}.items()),
        ]),
    ])

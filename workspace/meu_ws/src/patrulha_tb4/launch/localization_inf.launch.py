"""Localização oficial do TurtleBot 4 Humble com o timeout de bond do laboratório.

O bond_timeout escrito no localization_inf.yaml não chega ao gerente de ciclo de vida: o
localization_launch.py do Nav2 não lhe passa o arquivo de parâmetros, e ele ficava com o padrão
de 4 s. No robô, em 2026-11-25, o AMCL foi derrubado por isso ("after not receiving a heartbeat
for 4000 ms"). O SetParameter entrega o valor a todos os nós do grupo, gerente incluído.
"""
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetParameter


def generate_launch_description():
    oficial = (get_package_share_directory('turtlebot4_navigation')
               + '/launch/localization.launch.py')
    argumentos = ('namespace', 'map', 'params')
    return LaunchDescription(
        [DeclareLaunchArgument('namespace', default_value='')]
        + [DeclareLaunchArgument(nome) for nome in argumentos[1:]]
        + [GroupAction([
            SetParameter('bond_timeout', 120.0),  # o mesmo do Nav2 (navigation_inf.launch.py)
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(oficial),
                launch_arguments={n: LaunchConfiguration(n) for n in argumentos}.items()),
        ])])

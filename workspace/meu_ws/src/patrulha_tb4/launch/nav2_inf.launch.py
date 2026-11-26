"""Nav2 do TurtleBot 4 Humble com o timeout de bond do laboratório.

Reproduz o namespace e os remapeamentos de scan do launch oficial do TB4.
Inclui uma cópia pontual do navigation_launch.py Humble para aplicar bond_timeout.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace, SetRemap


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    parametros = LaunchConfiguration('params_file')
    navegacao = '/workspace/meu_ws/src/patrulha_tb4/launch/navigation_inf.launch.py'
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('params_file'),
        GroupAction([
            PushRosNamespace(namespace),
            SetRemap([namespace, '/global_costmap/scan'], [namespace, '/scan']),
            SetRemap([namespace, '/local_costmap/scan'], [namespace, '/scan']),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(navegacao),
                launch_arguments={
                    'namespace': namespace,
                    'params_file': parametros,
                    'use_composition': 'False',
                }.items(),
            ),
        ]),
    ])

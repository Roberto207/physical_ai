"""Gazebo (Ignition Fortress) SEM janela, com o TurtleBot 4 simulado (SIM-01, SIM-01b).

Argumentos: world (padrão maze), model (standard ou lite), namespace, x, y, z, yaw.

Por que não usar direto o turtlebot4_ignition.launch.py oficial: no Humble ele não tem modo só
servidor, e o ignition.launch.py que ele inclui sempre abre a interface gráfica (ign_args com
--gui-config). Este arquivo repete o que o ignition.launch.py oficial faz (ramo humble de
github.com/turtlebot/turtlebot4_simulator, lido em 2026-11-18): as variáveis de recurso, o
Gazebo e a ponte do /clock. A diferença é o "-s" (só o servidor) e o "--headless-rendering"
(o lidar e a câmera renderizam sem tela). O robô, a doca e os nós da Create 3 vêm do
turtlebot4_spawn.launch.py oficial, sem mudança.

SLAM, localização, Nav2 e RViz ficam desligados aqui: cada um é um serviço próprio do
infra/compose/sim.yaml, igual ao robô real.

As buscas de pacote usam FindPackageShare, que só resolve na hora de rodar. Assim o
"ros2 launch lab_tb4 gazebo.launch.py --show-args" funciona mesmo sem o simulador instalado.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _share(pacote, *partes):
    return PathJoinSubstitution([FindPackageShare(pacote), *partes])


def generate_launch_description():
    argumentos = [
        DeclareLaunchArgument('world', default_value='maze',
                              description='mundo: maze, depot ou warehouse'),
        DeclareLaunchArgument('model', default_value='standard', choices=['standard', 'lite'],
                              description='modelo do TurtleBot 4'),
        DeclareLaunchArgument('namespace', default_value='', description='namespace do robô'),
    ] + [DeclareLaunchArgument(eixo, default_value='0.0', description=f'pose inicial: {eixo}')
         for eixo in ('x', 'y', 'z', 'yaw')]

    # Mesmo conteúdo das duas variáveis do ignition.launch.py oficial. O "share/<pacote>/.."
    # é a pasta share, que é o que o oficial monta com Path(...).parent.
    recursos = SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', [
        _share('turtlebot4_ignition_bringup', 'worlds'), ':',
        _share('irobot_create_ignition_bringup', 'worlds'), ':',
        _share('turtlebot4_description', '..'), ':',
        _share('irobot_create_description', '..')])
    plugins = SetEnvironmentVariable('IGN_GUI_PLUGIN_PATH', [
        _share('turtlebot4_ignition_gui_plugins', 'lib'), ':',
        _share('irobot_create_ignition_plugins', 'lib')])

    # -s: só o servidor (sem GUI, SIM-01b). -r: começa rodando. -v 2: log de avisos e erros.
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_share('ros_ign_gazebo', 'launch', 'ign_gazebo.launch.py')),
        launch_arguments=[('ign_args', [LaunchConfiguration('world'), '.sdf',
                                        ' -s -r -v 2 --headless-rendering'])])

    relogio = Node(package='ros_gz_bridge', executable='parameter_bridge', name='clock_bridge',
                   output='screen',
                   arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'])

    robo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            _share('turtlebot4_ignition_bringup', 'launch', 'turtlebot4_spawn.launch.py')),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'model': LaunchConfiguration('model'),
            'use_sim_time': 'true',
            'rviz': 'false', 'slam': 'false', 'nav2': 'false', 'localization': 'false',
            'x': LaunchConfiguration('x'), 'y': LaunchConfiguration('y'),
            'z': LaunchConfiguration('z'), 'yaw': LaunchConfiguration('yaw'),
        }.items())

    return LaunchDescription(argumentos + [recursos, plugins, gazebo, relogio, robo])

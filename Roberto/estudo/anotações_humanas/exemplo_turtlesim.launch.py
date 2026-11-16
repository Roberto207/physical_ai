"""Exemplo de launch file para estudo: duas tartarugas, uma imitando a outra.

Um comando só (`ros2 launch`) sobe TRÊS programas:
  1. turtlesim_node no namespace /turtlesim1  (a tartaruga que você comanda)
  2. turtlesim_node no namespace /turtlesim2  (a tartaruga que imita)
  3. mimic                                     (lê a posição da 1 e comanda a 2)

Um launch file Python tem sempre a mesma forma:
  - uma lista de ações (nós, argumentos, mensagens);
  - uma função generate_launch_description() que devolve essa lista.
O `ros2 launch` procura exatamente por essa função.

Como rodar (ver o passo a passo no fim do arquivo):
  ros2 launch /workspace/exemplo_turtlesim.launch.py
  ros2 launch /workspace/exemplo_turtlesim.launch.py cor_fundo:=200
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # PARTE 1: ARGUMENTOS
    # O que dá para escolher na linha de comando, no formato nome:=valor.
    # Aqui: o tom de vermelho do fundo da primeira janela (0 a 255).
    cor_fundo = DeclareLaunchArgument(
        'cor_fundo',
        default_value='69',  # o padrão do turtlesim
        description='Vermelho do fundo da tartaruga 1 (0 a 255)',
    )

    # PARTE 2: MENSAGEM
    # Aparece no terminal quando o launch começa. Útil para avisar o que vai acontecer.
    aviso = LogInfo(msg=['Subindo 2 tartarugas e o mimic. Fundo vermelho = ',
                         LaunchConfiguration('cor_fundo')])

    # PARTE 3: NÓS
    # Cada Node é o equivalente a um `ros2 run PACOTE EXECUTAVEL`.

    # Nó 1: a tartaruga que você comanda.
    # O namespace evita conflito de nomes: os tópicos viram /turtlesim1/turtle1/...
    # parameters: o mesmo que `--ros-args -p background_r:=...`
    # O ParameterValue converte o texto do argumento para número inteiro.
    tartaruga1 = Node(
        package='turtlesim',
        executable='turtlesim_node',
        namespace='turtlesim1',
        name='sim',
        parameters=[{'background_r': ParameterValue(
            LaunchConfiguration('cor_fundo'), value_type=int)}],
    )

    # Nó 2: a tartaruga que imita. Mesmo executável, outro namespace e outro nó.
    # Prova de que um executável pode virar vários nós.
    tartaruga2 = Node(
        package='turtlesim',
        executable='turtlesim_node',
        namespace='turtlesim2',
        name='sim',
    )

    # Nó 3: o mimic liga as duas.
    # remappings: troca o nome de um tópico, o mesmo que `-r de:=para`.
    #   o mimic escuta  input/pose     -> ligamos à posição da tartaruga 1
    #   o mimic publica output/cmd_vel -> ligamos ao comando da tartaruga 2
    mimic = Node(
        package='turtlesim',
        executable='mimic',
        name='mimic',
        remappings=[
            ('/input/pose', '/turtlesim1/turtle1/pose'),
            ('/output/cmd_vel', '/turtlesim2/turtle1/cmd_vel'),
        ],
    )

    # PARTE 4: A LISTA FINAL
    # A ordem aqui é a de início, mas os nós sobem quase juntos.
    return LaunchDescription([cor_fundo, aviso, tartaruga1, tartaruga2, mimic])


# ----------------------------------------------------------------------------------------
# PASSO A PASSO (dentro do container do ros.sh)
#
# O container só enxerga a pasta workspace/ do projeto (como /workspace). Então copie
# este arquivo para lá, no seu computador:
#     cp estudo/anotações_humanas/exemplo_turtlesim.launch.py workspace/
#
# Terminal 1 (infra/docker/ros.sh):
#     ros2 launch /workspace/exemplo_turtlesim.launch.py
#   -> abrem 2 janelas de tartaruga.
#
# Terminal 2 (infra/docker/ros.sh de novo):
#     ros2 node list
#   -> /mimic, /turtlesim1/sim, /turtlesim2/sim
#     ros2 topic pub -r 1 /turtlesim1/turtle1/cmd_vel geometry_msgs/msg/Twist \
#         "{linear: {x: 2.0}, angular: {z: 1.8}}"
#   -> a tartaruga 1 anda em círculo e a 2 imita.
#
# Para listar os argumentos do launch:
#     ros2 launch /workspace/exemplo_turtlesim.launch.py --show-args
# Para parar tudo: Ctrl+C no terminal 1.
# ----------------------------------------------------------------------------------------

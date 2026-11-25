"""Inicia o nó de linguagem natural. Mesmo nome e parâmetros do launch do tutorial oficial.

Para o robô real use infra/docker/lab.sh robo llm: num "docker stop" o ros2 launch morre
antes de o nó cancelar a meta.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

ARGUMENTOS = (
    ('model_name', 'qwen2.5:1.5b', str, 'modelo do Ollama'),
    ('parking_brake', 'true', bool, 'freio: false MOVE O ROBÔ'),
    ('ollama_url', 'http://127.0.0.1:11434/api/chat', str, 'API de chat do Ollama'),
    ('mapa', '/mapas/mapa_lab_novo.yaml', str, 'mapa para conferir coordenadas'),
    ('arquivo_pontos', '/workspace/patrulha_oficial/patrol_loop.py', str,
     'de onde ler DOCA e PONTOS'),
    ('bateria_simulada', '-1.0', float, 'carga de 0 a 1 para testar sem robô; -1 usa a real'),
)


def generate_launch_description():
    declaracoes = [DeclareLaunchArgument(nome, default_value=padrao, description=texto)
                   for nome, padrao, _, texto in ARGUMENTOS]
    parametros = {nome: ParameterValue(LaunchConfiguration(nome), value_type=tipo)
                  for nome, _, tipo, _ in ARGUMENTOS}
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='', description='ex.: /robot1'),
        *declaracoes,
        Node(package='llm_tb4', executable='natural_language_nav', output='screen',
             emulate_tty=True, namespace=LaunchConfiguration('namespace'),
             # Tempo para o nó cancelar a meta antes de o launch forçar o encerramento.
             sigterm_timeout='8', sigkill_timeout='5',
             parameters=[parametros]),
    ])

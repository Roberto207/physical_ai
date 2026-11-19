"""Um cenário do teste L1 (spec patrol-inf, TST-03 a TST-05 e PAT-xx): simulador leve + patrulha.

Argumentos:
  cenario   nome em config/cenarios_l1.yaml (obrigatório)
  pasta     onde a patrulha grava o log JSONL e o vigia grava ambiente.txt e sinal.txt

Chamado pelo infra/docker/teste_l1.sh, que roda um container por cenário e dá o veredito.
Substitui o antigo infra/docker/l1_dentro.sh (tag jazzy-final): a mesma sequência, em launch.

Sequência (a mesma do script antigo):
  0 s   sim_leve.launch.py (loopback, map_server, Nav2), se subir_nav2; a base falsa sobe
        dentro dele aos 15 s, se subir_base. O vigia_l1 sobe já aqui, para ver no /rosout um
        "Aborting bringup" do Nav2 (SIM-06)
  18 s  a patrulha (patrulha.launch.py, sem mudança: AMB-01). O tempo-limite do vigia conta
        daqui
O fim: quando o vigia sai (ponto esperado, tempo-limite ou Nav2 que não subiu), o launch
encerra. Quando a patrulha sai sozinha, o patrulha.launch.py já encerra o launch.

O mapa vem da configuração da patrulha (campo mapa, inclusive pkg://), como antes.
"""
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription,
                            OpaqueFunction, RegisterEventHandler, TimerAction)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from lab_tb4.cenarios import argumentos_launch, carregar as carregar_cenarios

ESPERA_PATRULHA_S = 18.0   # 15 s do Nav2 + 3 s da base falsa, como no l1_dentro.sh


def _montar(contexto):
    nome = LaunchConfiguration('cenario').perform(contexto)
    pasta = LaunchConfiguration('pasta').perform(contexto)
    lab = get_package_share_directory('lab_tb4')
    cenarios = carregar_cenarios(os.path.join(lab, 'config', 'cenarios_l1.yaml'))
    if nome not in cenarios:
        raise RuntimeError(f'cenário desconhecido: {nome} (conhecidos: {", ".join(cenarios)})')
    c = cenarios[nome]

    config = os.path.join(get_package_share_directory('patrulha_tb4'), 'config', c['config'])
    from patrulha_tb4.config import carregar as carregar_config
    mapa = carregar_config(config).mapa
    # O antigo l1_dentro.sh imprimia estas duas linhas no container.log; o veredito não as usa.
    print(f'config: {config}\nmapa: {mapa}', flush=True)

    acoes = []
    if c['subir_nav2']:
        # Os parâmetros da base vão como YAML de uma linha, que o sim_leve lê de volta.
        base = yaml.safe_dump(c['base'], default_flow_style=True).strip()
        argumentos = [('map', mapa), ('subir_base', str(c['subir_base']).lower()), ('base', base)]
        acoes.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(lab, 'launch', 'sim_leve.launch.py')),
            launch_arguments=argumentos + argumentos_launch(c['nav2_extra'])))
    elif c['subir_base']:
        acoes.append(Node(package='lab_tb4', executable='base_falsa', name='fake_tb4_base',
                          output='screen', parameters=[c['base']]))

    patrulha = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('patrulha_tb4'), 'launch',
                         'patrulha.launch.py')),
        launch_arguments=[('config', config), ('pasta_log', pasta)]
        + argumentos_launch(c['patrulha_extra']))
    vigia = Node(package='lab_tb4', executable='vigia_l1', name='vigia_l1', output='screen',
                 parameters=[{'cenario': nome, 'pasta': pasta, 'limite_s': float(c['limite_s']),
                              'sinal_no_fim': bool(c['sinal_no_fim']),
                              'olhar_nav2': bool(c['subir_nav2']),
                              'espera_s': ESPERA_PATRULHA_S}])
    fim = RegisterEventHandler(OnProcessExit(
        target_action=vigia, on_exit=[EmitEvent(event=Shutdown(reason='vigia encerrou'))]))
    acoes += [vigia, fim, TimerAction(period=ESPERA_PATRULHA_S, actions=[patrulha])]
    return acoes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('cenario', description='nome do cenário (config/cenarios_l1.yaml)'),
        DeclareLaunchArgument('pasta', default_value='/evidencias',
                              description='pasta de evidências (JSONL, ambiente.txt, sinal.txt)'),
        OpaqueFunction(function=_montar),
    ])

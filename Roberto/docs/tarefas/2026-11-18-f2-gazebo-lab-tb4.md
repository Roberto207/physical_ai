# Tarefa: F2 da migração para Humble (Gazebo e pacote `lab_tb4`)

**Data:** 2026-11-18
**Spec:** `specs/migracao-humble/`, fase F2. Requisitos: LCH-01, LCH-03, SIM-01, SIM-01b, SIM-02, SIM-02b.
**Situação:** código pronto. **O teste de fumaça do Gazebo (SIM-01) só roda no PC do lab.**

## 1. Resposta direta

Nasceu o pacote `lab_tb4`, onde ficam os launches de ambiente. O primeiro é o `gazebo.launch.py`, que sobe o Ignition Fortress só como servidor (`-s`, sem interface gráfica) com o TurtleBot 4 simulado. Ele substitui o truque antigo de montar o nosso arquivo por cima de um arquivo de `/opt/ros/jazzy/share/`. A base falsa virou um nó instalado: `ros2 run lab_tb4 base_falsa`. O `sim.yaml` deixou de escrever a distro.

## 2. O pipeline do serviço `gazebo`

1. `docker compose -f infra/compose/sim.yaml up -d gazebo` (ou `./lab.sh sim subir gazebo`).
2. O entrypoint carrega o ROS e, com `COMPILAR_WS=lab_tb4`, compila o `lab_tb4` em `/tmp` (alguns segundos).
3. O comando sobe o Xvfb (tela falsa `:99`) e executa `ros2 launch lab_tb4 gazebo.launch.py world:=${MUNDO:-maze}`.
4. O `gazebo.launch.py`:
   - define `IGN_GAZEBO_RESOURCE_PATH` e `IGN_GUI_PLUGIN_PATH`, com o mesmo conteúdo do `ignition.launch.py` oficial (ramo `humble`, lido em 2026-11-18);
   - inclui o `ros_ign_gazebo/ign_gazebo.launch.py` com `ign_args = maze.sdf -s -r -v 2 --headless-rendering`;
   - sobe a ponte do `/clock` (`ros_gz_bridge`);
   - inclui o `turtlebot4_spawn.launch.py` oficial, com `slam`, `nav2`, `localization` e `rviz` desligados. Ele cria o robô e a doca no mundo e sobe os nós da Create 3 e do TurtleBot 4 (bateria, doca, lidar).
5. SLAM, localização, Nav2 e RViz continuam como serviços separados, iguais aos do `robo.yaml`.

Por que um launch nosso, e não o `turtlebot4_ignition.launch.py` oficial: no Humble, o oficial sempre abre a interface gráfica (`--gui-config`) e não tem modo só servidor. O `--headless-rendering` existe no Fortress (opção do `ign gazebo`, lida no `cmdgazebo.rb.in` do ramo `ign-gazebo6`). O Xvfb fica como garantia, porque foi o que funcionou no Jazzy em 16/11.

As buscas de pacote do launch são `FindPackageShare`, que só resolvem na hora de rodar. Por isso o `--show-args` funciona até numa imagem sem o simulador.

## 3. Outras mudanças no `sim.yaml`

| Serviço | Mudança |
|---|---|
| `localizacao` | O mapa padrão vem de `$(ros2 pkg prefix turtlebot4_navigation)/share/.../maps/maze.yaml`, resolvido no container. O `MAPA` do host entra pela interpolação do Compose. Antes, o caminho era `/opt/ros/jazzy/...` escrito no arquivo |
| `rviz` | `view_robot.launch.py` (o Humble não tem `view_navigation`) |
| `teleop` | `stamped:=false`: a Create 3 simulada do Humble recebe `Twist`, como o robô real |
| `patrulha` | `COMPILAR_WS=patrulha_tb4`; o bloco de `colcon build` saiu |
| todos | Sem `source /opt/ros/...`: o entrypoint carrega |

## 4. Verificado e não verificado

| Item | Situação |
|---|---|
| `docker compose config` do `sim.yaml` | **Medido** |
| O `MAPA` do host chega ao comando da `localizacao` | **Medido** (`MAPA=/mapas/x.yaml docker compose ... config`) |
| Os 6 serviços comuns existem nos dois arquivos (SIM-02) | **Medido** (`config --services`: o sim só tem a mais o `gazebo` e o `undock`) |
| `ruff` e `py_compile` do launch | **Medido** |
| Base falsa: mesmo código, os mesmos 11 parâmetros | **Medido** por `git mv` (o diff é só a docstring) |
| SIM-01: `/scan`, `/odom`, `/tf` e `/dock_status` em 90 s; sem processo de GUI | **Não verificado**: no PC, `./lab.sh sim subir gazebo`, depois `./lab.sh sim compose run --rm ferramentas ros2 topic echo --once /scan` (e os outros) e `pgrep -af 'ign gazebo'` no container |
| SIM-01c: `/battery_state` em 60 s simulados | **Não verificado** (PC) |

## 5. Efeito prático

- Para mapear no Gazebo, o roteiro de 16/11 continua igual: `./lab.sh sim subir gazebo slam rviz`, `undock`, `teleop`, `salvar`.
- A medição M-GZH (o fator de tempo real e o resto) continua só com o seu pedido. O teste de fumaça acima só confere se os tópicos chegam.

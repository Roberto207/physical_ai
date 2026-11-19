# Tarefa: F1 da migração para Humble (o modo robo)

*Nota (2026-11-19): os caminhos deste documento são da época. Depois do enxugamento (`specs/enxugamento/SPEC.md`), o mapa das pastas está no `README.md` da raiz.*

**Data:** 2026-11-18
**Spec:** `specs/migracao-humble/`, fase F1. Requisitos: IMG-01 a IMG-06, PRE-02, SEG-01 a SEG-06, CFG-01 a CFG-05.
**Situação:** código pronto e conferido no notebook. **A V1 (build), a SEG-01 com imagem real e a V5 (robô) dependem do PC do laboratório.** O robô não recebeu nada.

## 1. Resposta direta

O modo `robo` agora roda em imagens Humble, a mesma distro do robô. Três peças fazem isso:

- o Dockerfile parte de `ros:humble-ros-base`;
- um entrypoint carrega o ROS pela variável `ROS_DISTRO` da imagem, e os compose deixam de escrever a distro;
- o `lab.sh` recusa qualquer ação do modo `robo` se alguma imagem do `robo.yaml` não for Humble.

O perfil lento do Nav2 foi refeito a partir do arquivo oficial do Humble. As configurações da patrulha passaram a apontar o mapa por `pkg://`, sem a distro no caminho.

## 2. O que mudou, arquivo por arquivo

| Arquivo | Mudança | Por quê |
|---|---|---|
| `infra/docker/Dockerfile` | `FROM ros:humble-ros-base`; os alvos `base`, `robo`, `sim` e `llm`; sem o `completa`, `turtlesim`, `demo_nodes_py`, `x11-apps` e `mesa-utils`; `sim` com `turtlebot4_simulator` (Fortress), `tf-transformations`, `transforms3d` e `xvfb`; `llm` com os tutoriais `-b humble` | IMG-01 a IMG-05. O `sim` já traz o que o loopback vendorizado da F3 importa |
| `infra/docker/entrypoint.sh` (novo) | Carrega `/opt/ros/$ROS_DISTRO` e `/opt/tb4_ws`; com `COMPILAR_WS=a,b`, compila esses pacotes em `/tmp` e carrega o resultado; `exec "$@"` | IMG-03. Também tira do compose o bloco de `colcon build` repetido |
| `infra/docker/construir_imagem.sh` | A conferência de RAM vem antes de tudo (IMG-06); a imagem Jazzy com o mesmo nome ganha a tag `physical-ai:jazzy-<alvo>` antes do build (PRE-02); sem `apelidos` e sem `completa` | O `apelidos` só existia para o `docker commit` do notebook, que deixou de construir |
| `infra/docker/lab.sh` | `distro_ok()` lê o `ROS_DISTRO` de cada imagem do `robo.yaml` (`docker compose config --images` + `docker image inspect`) e, se algum não for `humble`, recusa a ação com o código 1. O `parar` com imagem errada só faz o `down` | SEG-01. É a checagem que faltou em 16/11 |
| `infra/compose/robo.yaml` | Os comandos viram `ros2 launch ...` direto; `bash -c` só onde há lógica de shell (teste do mapa, `SIM`); a patrulha usa `COMPILAR_WS`; o `nav2` usa o perfil direto, sem a cópia com `sed`; o teleop usa `stamped:=false` fixo; o `rviz` usa o `view_robot.launch.py` | SEG-02 a SEG-06, IMG-04. O `view_navigation` não existe no Humble |
| `patrulha_tb4/config/nav2_inf_devagar.yaml` | Regenerado do `nav2.yaml` do `turtlebot4_navigation` 1.0.5 (ramo `humble`), mudando só `max_velocity[0]` (0,15) e `min_velocity[0]` (−0,15) | CFG-04. O perfil Jazzy tinha `enable_stamped_cmd_vel` e `docking_server`, que não existem no Nav2 Humble |
| `patrulha_tb4/patrulha_tb4/config.py` | `resolver_pkg()`: `pkg://<pacote>/<caminho>` vira `<share>/<caminho>` pelo ament_index. Sem o pacote: `mapa_pacote_inexistente`. Sem ROS: `pkg_sem_ros` | CFG-01, CFG-02, CFG-02b. O `import` fica dentro da função para o L0 rodar sem ROS |
| 4 configs (`leve_reduzido`, `teste_tempo_curto`, `gazebo_maze`, `warehouse_original`) | `mapa: pkg://turtlebot4_navigation/maps/<nome>.yaml` | CFG-03 |
| `test/test_config.py` | 4 testes novos (CFG-01, 02, 02b, e "sem `pkg://` não muda") e o teste das configs do pacote com um ament_index falso | O CFG-05 permite mexer só neste arquivo de teste |

## 3. Como o `use_sim_time: True` do arquivo oficial não afeta o robô

O `nav2.yaml` do Humble vem com `use_sim_time: True`. O `nav2.launch.py` do `turtlebot4_navigation` passa o argumento `use_sim_time` (padrão `false`) para o `navigation_launch.py` do Nav2. Esse launch reescreve o parâmetro em todos os nós ao carregar o YAML. Lido no código do ramo `humble` em 2026-11-18. O comentário está no cabeçalho do perfil.

## 4. Verificado e não verificado

| Item | Situação |
|---|---|
| Atributos do `TurtleBot4Navigator` e do `BasicNavigator` Humble que o `no_patrulha.py` usa (V2) | **Lido** no código Humble: os 9 existem com os mesmos nomes. O `no_patrulha.py` não mudou |
| L0: 134 testes, rastreio com 31 requisitos | **Medido** no notebook |
| Diff do perfil do Nav2 contra o oficial Humble: só os 2 valores | **Medido** (comparação dos YAML carregados) |
| `docker compose config` do `robo.yaml`; sem `--profile`, zero serviços | **Medido** |
| G4 (sem `stamped:=true` nem `enable_stamped_cmd_vel: true`) | **Medido** |
| `bash -n` do `lab.sh` | **Medido** |
| V1: o build das imagens Humble | **Não verificado**: só no PC do lab (`construir_imagem.sh base robo`) |
| SEG-01 com uma imagem Jazzy de verdade | **Não verificado**: no PC, antes do primeiro build a `physical-ai:base` ainda é Jazzy, e o `lab.sh robo estado` deve recusar |
| V5: o robô | **Não verificado**. Só com a sua permissão |

## 5. Efeito prático

- No PC do lab: `infra/docker/construir_imagem.sh base robo`. Isso guarda as Jazzy como `jazzy-base` e `jazzy-robo` e constrói as Humble. Construa as duas juntas: se só a `robo` for construída, a `base` continua Jazzy, e o `lab.sh robo` recusa (SEG-01).
- O aviso "não use o `lab.sh robo`" continua até a V5 passar (DOC-01).

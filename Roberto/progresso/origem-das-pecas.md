# De onde vem cada parte da simulação do teste do `patrol_loop`

Última atualização: 2026-11-10. Vale para o teste de 9/nov, rodado com `infra/docker/treino_leve.sh iniciar --rviz --patrulha`.

## Resposta direta

No teste, o **programa de patrulha, o Nav2, o mapa e o formato do robô são oficiais** (vêm de pacotes do ROS, do Nav2 e do TurtleBot 4). O **movimento** do robô é calculado por um simulador do Nav2 (sem física). A **bateria, a doca e a localização foram inventadas por nós**. O simulador leve não é um mundo: é a peça que deixa o Nav2 rodar sem Gazebo.

## A cena do dia a dia

Um **ensaio de teatro com cenário de papelão**. A planta do galpão é de verdade (o mapa). O ator que sabe andar sem bater é de verdade (o Nav2). Mas ninguém anda de fato: um assistente empurra uma peça sobre a planta conforme o ator manda (o simulador leve). E o narrador que anuncia "a bateria está em 40%" e "encaixei na doca" somos nós, lendo um roteiro (a base falsa).

## Quadro geral: cada parte, de onde vem e se é real

| # | Parte | O que faz no teste | Origem | Real ou falso |
|---|---|---|---|---|
| 1 | Ambiente | Ubuntu 24.04 com ROS 2 Jazzy | Imagem `physical-ai:jazzy` (`infra/docker/Dockerfile`), sobre `ros:jazzy-ros-base` | Real |
| 2 | Script que sobe tudo | Liga o Nav2, a base falsa e a patrulha | `infra/docker/treino_leve.sh` | Nosso |
| 3 | **Nav2** | Planeja a rota, desvia, recebe os destinos (`navigate_to_pose`) | Pacote `nav2_bringup`, launch `tb4_loopback_simulation.launch.py` | **Real** |
| 4 | **Simulador leve** | Calcula onde o robô estaria a partir do `/cmd_vel` | Pacote `nav2_loopback_sim`, nó `/loopback_simulator` | Movimento calculado, **sem física nem sensores de verdade** |
| 5 | **Mapa** | O espaço onde o robô navega | Arquivo `warehouse.yaml`, no pacote `turtlebot4_navigation`. O `map_server` (do Nav2) o publica em `/map` | Arquivo real, **2D**, de um mundo simulado |
| 6 | **Formato do robô** | O desenho do TurtleBot 4 no RViz, e as medidas para o Nav2 | `turtlebot4.urdf.xacro`, pacote `nav2_minimal_tb4_description`, entregue ao `robot_state_publisher` | Descrição real (32 peças e 31 ligações) |
| 7 | RViz | Janela que desenha o mapa, o robô e a rota | `rviz2`, aberto pelo mesmo launch (`use_rviz:=True`) | Só mostra, não simula nada |
| 8 | **Bateria** (`/battery_state`) | Informa a carga e a faz cair | `infra/tools/fake_tb4_base.py` | **Falsa (nossa)** |
| 9 | **Doca** (`/dock_status`, ações `/dock` e `/undock`) | Diz se está na base e "encaixa" na hora | `infra/tools/fake_tb4_base.py`, com os tipos de mensagem reais da iRobot (`irobot_create_msgs`) | **Falsa (nossa)** |
| 10 | **Localização** (`/amcl_pose`, `amcl/get_state`) | Responde "localização ativa" para o Nav2 aceitar iniciar | `infra/tools/fake_tb4_base.py` | **Falsa (nossa)**. A posição verdadeira vem do item 4 |
| 11 | **Programa de patrulha** | Decide ir aos pontos, olha a bateria, volta à base | `patrol_loop`, pacote `turtlebot4_python_tutorials`, compilado do GitHub (branch `jazzy`) em `/opt/tb4_ws` | **Real, sem nenhuma alteração** |
| 12 | API de navegação do `patrol_loop` | `startToPose`, `dock`, `undock`, `getDockedStatus` | `TurtleBot4Navigator` (pacote `turtlebot4_navigation`, segundo o manual) sobre o `BasicNavigator` (`nav2_simple_commander`) | Real. **Não abri o arquivo do `TurtleBot4Navigator`**, então a origem exata dele é pelo manual |
| 13 | Cenário do teste | Bateria inicial de 30%, descarga de 0,1% por segundo, carga de 5% por segundo | Variáveis do `treino_leve.sh`, passadas à base falsa | Escolha nossa |

Sobre o item 11: os limites de bateria (0,95, 0,20 e 0,10) foram lidos do código na semana 3. Os destinos `(-5, 1)`, `(-5, -23)`, `(9, -23)` e o ponto de aproximação da doca `(-1, 1)` foram vistos no log, e **não conferi em que linha do código eles estão definidos**.

## Quem conversa com quem

```
patrol_loop (real)
   |-- lê /battery_state ............................ fake_tb4_base (nosso)
   |-- ações /dock e /undock ........................ fake_tb4_base (nosso)
   |-- ação navigate_to_pose ----> Nav2 (real)
                                     |  usa o mapa de /map (map_server, arquivo do turtlebot4_navigation)
                                     |  manda /cmd_vel ----> loopback_simulator (calcula a posição)
                                     +<--- posição (tf) ----+

RViz (só mostra) <-- /map, tf e /robot_description (robot_state_publisher + URDF do TurtleBot 4)
```

## O que o teste prova e o que não prova

| Prova | Não prova |
|---|---|
| A lógica de decisão do `patrol_loop` (ir, olhar a bateria, voltar) | Bateria real: a nossa cai na fórmula que escrevemos |
| Como o `patrol_loop` usa o Nav2 e o Navigator | Docking real: o nosso "encaixa" na hora, sem sensor nem alinhamento |
| O comportamento do Nav2 sobre um mapa dado | Sensores (lidar e câmera), física e atrito |
| Os defeitos do código do `patrol_loop` (por exemplo, bateria só vista entre destinos) | A localização real (o AMCL é falso) |

## Duas consequências diretas dessa origem

1. **O `Robot failed to dock`** (ver `patrol-loop.md`) provavelmente vem da parte falsa (item 9): a base falsa só atualiza o `/dock_status` uma vez por segundo, e o `patrol_loop` o leu logo depois do dock. É hipótese, não confirmada.
2. **A bateria começou em 85%**, e não em 30%, por causa da parte falsa (itens 8 e 13): a base falsa carrega a 5% por segundo enquanto o robô está nela, e o sistema levou cerca de 20 s para subir.

Já o defeito de a bateria zerar no trecho de volta é do **`patrol_loop` (item 11)**, e não do ambiente.

## Como conferir cada coisa (dentro do container)

Estes comandos são o caminho normal para checar a origem. Não os rodei para este documento, exceto onde o resultado já foi observado em sessões anteriores.

| Quero saber | Comando |
|---|---|
| Que nós existem | `ros2 node list` (apareceram `/loopback_simulator`, `/map_server`, `/fake_tb4_base`, `/bt_navigator` e outros) |
| De onde vem um pacote | `ros2 pkg prefix NOME` |
| O que um nó publica e assina | `ros2 node info /NOME` |
| Quem publica a bateria | `ros2 topic info /battery_state` |

## Efeito prático

Quando alguém perguntar "o que você simulou?", a resposta é: a lógica da patrulha, com o Nav2 e o mapa reais e o robô calculado. Quando perguntarem "e a bateria e a doca?", a resposta é que são scripts nossos, e que só o robô real ou o Gazebo (onde a base da iRobot é simulada) validam isso. É por isso que a primeira entrega é parcial, e que o teste no robô é um gate à parte.

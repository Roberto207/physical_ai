# Fontes e stack

## Stack (ADR-001 e ADR-002)

| Camada | Escolha |
|---|---|
| Robô | TurtleBot 4 (Clearpath Robotics). Modelo (padrão ou Lite) a confirmar: o log do robô diz `Device type: OAK-D-PRO`, a câmera do modelo padrão |
| ROS | **ROS 2 Humble**, Ubuntu 22.04, em container Docker (`physical-ai:<alvo>`: `base`, `robo`, `sim`). O Jazzy ficou na tag git `jazzy-final` |
| Navegação | Nav2 com o TurtleBot 4 Navigator (`TurtleBot4Navigator`, do pacote `turtlebot4_navigation`) |
| Simulador principal | Gazebo (Ignition) **Fortress**, sem janela, no PC do laboratório. Pacote `lab_tb4` em `workspace/meu_ws/src/lab_tb4` |
| Simulador L1 | `nav2_loopback_sim` **vendorizado** em `workspace/meu_ws/src/terceiros/nav2_loopback_sim`, com base, bateria e AMCL falsos, para injeção de falhas |
| Patrulha no robô | `workspace/patrulha_oficial/` (adaptação do exemplo oficial) |
| Patrulha com recarga | Pacote `patrulha_tb4` (lógica em Python puro, testada em L0), anterior |
| Rede com o robô | Fast DDS com Discovery Server no robô, domínio 0, namespace `/robot1` (`docs/contexto/maquinas.md`) |
| LLM | **Ollama** com o modelo `qwen2.5:1.5b`, gratuito e local (decidido em 25/11) |
| Segurança da LLM | `workspace/meu_ws/src/llm_tb4/llm_tb4/validar_acao.py`: a LLM escolhe ações discretas validadas, sem `exec` |

## Referências oficiais: consultar primeiro

Quando não souber como fazer uma atividade, ou ao planejar uma etapa, comece por estes dois links:

| Link | O que há |
|---|---|
| [Resources do manual do TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/overview/resources.html) | Índice oficial dos repositórios e documentos: ROS 2, Nav2, SLAM Toolbox, pacotes do TurtleBot 4, Create 3, câmera e lidar |
| [turtlebot4_tutorials](https://github.com/turtlebot/turtlebot4_tutorials/tree/humble) (ramo `humble`) | Código pronto para usar de base. Dele saiu a patrulha que roda no robô (`workspace/patrulha_oficial/`). Traz `turtlebot4_python_tutorials`, `turtlebot4_cpp_tutorials` e `turtlebot4_openai_tutorials` |

Use o ramo `humble`, a distro do robô.

## Material recomendado pelo colega (Gabriel Santiago Vidal)

1. Vídeo sobre o hardware do TurtleBot 4 (o que vem no kit).
2. Playlist de primeiros passos (setup inicial e configuração do robô).
3. Vídeo de introdução ao ROS.
4. Canal Articulated Robotics (simulação e ROS).
5. Site da Clearpath Robotics (materiais complementares).

Setup no manual: Basic Setup e Simple Discovery. Os links, com o que foi verificado em cada um, estão nas anotações de estudo do Roberto, que ficam só no disco dele (fora do git).

## Conceitos que o colega ainda está revisando

Odometry, nodes, joints e os fundamentos de ROS 2, principalmente **actions**, que é como o Nav2 recebe os goals.

## Manual oficial

https://turtlebot.github.io/turtlebot4-user-manual/

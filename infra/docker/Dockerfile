# Família de imagens do projeto (ROS 2 Humble + TurtleBot 4), em camadas. Cada alvo começa do
# anterior, então o que é comum fica no disco uma vez só.
#
#   base   Nav2, SLAM, teleop e o que os nossos pacotes precisam. Sem janela.  -> physical-ai:base
#   robo   base + RViz (turtlebot4_desktop). Para o PC do lab com o robô.     -> physical-ai:robo
#   sim    robo + Ignition Fortress com o TB4 e as dependências do loopback.  -> physical-ai:sim
#   llm    base + tutoriais do LLM. Esqueleto da missão 2.                   -> physical-ai:llm
#
# Humble porque o robô do lab é Humble: nós Jazzy na rede dele derrubaram o serviço turtlebot4
# em 2026-11-16 (docs/decisoes/ADR-001-ros2-humble.md). A versão Jazzy deste arquivo está na
# tag git jazzy-final.
#
# Construa com ./construir_imagem.sh <alvo>, que confere a RAM antes (o "docker build" não tem
# teto de memória) e guarda as imagens Jazzy antigas como physical-ai:jazzy-<alvo>.
# Spec: specs/migracao-humble/ (DEFINE e DESIGN, seção 4).

# ---------------------------------------------------------------- base
FROM ros:humble-ros-base AS base
ENV DEBIAN_FRONTEND=noninteractive
# turtlebot4_navigation já traz Nav2 e slam_toolbox como dependências; os dois ficam explícitos
# para a imagem não quebrar sem aviso se isso mudar. ros-dev-tools traz o colcon, que compila
# os nossos pacotes quando o container sobe (COMPILAR_WS, ver entrypoint.sh).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-turtlebot4-navigation \
        ros-humble-nav2-bringup \
        ros-humble-nav2-simple-commander \
        ros-humble-slam-toolbox \
        ros-humble-irobot-create-msgs \
        ros-humble-teleop-twist-keyboard \
        ros-dev-tools python3-yaml python3-pytest \
    && rm -rf /var/lib/apt/lists/*
# O entrypoint carrega /opt/ros/$ROS_DISTRO (a imagem oficial define ROS_DISTRO=humble): assim os
# compose e os scripts não escrevem o nome da distro (IMG-03, IMG-04).
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

# ---------------------------------------------------------------- robo
FROM base AS robo
# turtlebot4_desktop traz o turtlebot4_viz (view_robot.launch.py) e o RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-turtlebot4-desktop \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------- sim
FROM robo AS sim
# turtlebot4_simulator: Ignition Fortress + o TB4 e a Create 3 simulados (bateria e doca da
# iRobot). tf-transformations e transforms3d: o que o nav2_loopback_sim vendorizado importa
# (workspace/meu_ws/src/terceiros/). Xvfb: a tela falsa onde o lidar do Gazebo renderiza, se o
# --headless-rendering não bastar na GPU do PC.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-turtlebot4-simulator \
        ros-humble-tf-transformations \
        python3-transforms3d \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------- llm
FROM base AS llm
# Esqueleto antigo da missão do LLM: só os tutoriais oficiais (ramo humble), como referência. Não é
# usado: o pacote llm_tb4 roda na imagem base e fala com o Ollama por HTTP (infra/compose/llm.yaml).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && bash -c "source /opt/ros/$ROS_DISTRO/setup.bash \
    && mkdir -p /opt/tb4_ws/src && cd /opt/tb4_ws/src \
    && git clone --depth 1 -b humble https://github.com/turtlebot/turtlebot4_tutorials.git \
    && cd /opt/tb4_ws \
    && colcon build --packages-select turtlebot4_python_tutorials turtlebot4_openai_tutorials"

# Família de imagens do projeto (ROS 2 Jazzy + TurtleBot 4), em camadas. Cada alvo começa do
# anterior, então o que é comum fica no disco uma vez só.
#
#   base      Nav2, SLAM, teleop e o que o nosso pacote precisa. Sem janela.  -> physical-ai:base
#   robo      base + RViz (turtlebot4_desktop). Para o PC do lab com o robô.  -> physical-ai:robo
#   sim       robo + Gazebo, simulador leve e os tutoriais (patrol_loop).     -> physical-ai:sim
#   llm       base + tutoriais do LLM. Esqueleto da missão 2.                 -> physical-ai:llm
#   completa  sim + tutoriais do LLM = a antiga imagem única.                 -> physical-ai:jazzy
#
# Construa com ./construir_imagem.sh <alvo>, que confere a RAM antes (o "docker build" não tem
# teto de memória). NOTEBOOK DO ROBERTO (7,4 GiB): não construa lá; a physical-ai:jazzy dele foi
# montada com "docker run --memory=2g" e "docker commit", e o script só cria os apelidos.
# Explicação: docs/tarefas/2026-11-16-compose-e-alvos.md

# ---------------------------------------------------------------- base
FROM ros:jazzy-ros-base AS base
ENV DEBIAN_FRONTEND=noninteractive
# turtlebot4_navigation já traz Nav2 e slam_toolbox como dependências (package.xml, ramo
# jazzy); os dois ficam explícitos para a imagem não quebrar sem aviso se isso mudar.
# ros-dev-tools traz o colcon, que compila o nosso pacote quando o container sobe.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-turtlebot4-navigation \
        ros-jazzy-nav2-bringup \
        ros-jazzy-nav2-simple-commander \
        ros-jazzy-slam-toolbox \
        ros-jazzy-irobot-create-msgs \
        ros-jazzy-teleop-twist-keyboard \
        ros-dev-tools python3-yaml python3-pytest \
    && rm -rf /var/lib/apt/lists/*
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
CMD ["bash"]

# ---------------------------------------------------------------- robo
FROM base AS robo
# turtlebot4_desktop traz o turtlebot4_viz (view_navigation.launch.py) e o RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-turtlebot4-desktop mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------- sim
FROM robo AS sim
# Gazebo + TurtleBot 4 simulado, o simulador leve do Nav2 (testes L1) e o Xvfb, a tela falsa
# que deixa o Gazebo renderizar o lidar sem janela.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-turtlebot4-simulator \
        ros-jazzy-irobot-create-nodes \
        ros-jazzy-nav2-loopback-sim \
        ros-jazzy-nav2-minimal-tb4-sim \
        ros-jazzy-turtlesim \
        ros-jazzy-demo-nodes-py \
        git x11-apps xvfb \
    && rm -rf /var/lib/apt/lists/*
# Os tutoriais não têm pacote apt para Jazzy: compilamos do GitHub. O patrol_loop oficial
# (turtlebot4_python_tutorials) é usado pelo treino_leve.sh.
RUN bash -c "source /opt/ros/jazzy/setup.bash \
    && mkdir -p /opt/tb4_ws/src && cd /opt/tb4_ws/src \
    && git clone --depth 1 -b jazzy https://github.com/turtlebot/turtlebot4_tutorials.git \
    && cd /opt/tb4_ws \
    && colcon build --symlink-install --packages-select turtlebot4_python_tutorials" \
    && echo "source /opt/tb4_ws/install/setup.bash" >> /root/.bashrc

# ---------------------------------------------------------------- llm
FROM base AS llm
# Esqueleto da missão do LLM: só os tutoriais oficiais. As bibliotecas do provedor de LLM
# entram aqui quando o provedor for decidido (pendência aberta).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && bash -c "source /opt/ros/jazzy/setup.bash \
    && mkdir -p /opt/tb4_ws/src && cd /opt/tb4_ws/src \
    && git clone --depth 1 -b jazzy https://github.com/turtlebot/turtlebot4_tutorials.git \
    && cd /opt/tb4_ws \
    && colcon build --symlink-install --packages-select turtlebot4_python_tutorials turtlebot4_openai_tutorials" \
    && echo "source /opt/tb4_ws/install/setup.bash" >> /root/.bashrc

# ---------------------------------------------------------------- completa
FROM sim AS completa
# A antiga imagem única (physical-ai:jazzy), que os scripts ros.sh, treino_leve.sh e
# teste_l1.sh usam. Só acrescenta os tutoriais do LLM ao que o sim já tem.
RUN bash -c "source /opt/ros/jazzy/setup.bash && cd /opt/tb4_ws \
    && colcon build --symlink-install --packages-select turtlebot4_python_tutorials turtlebot4_openai_tutorials"

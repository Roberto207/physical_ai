# ATENÇÃO: não rode "docker build" neste notebook. O build não tem limite de memória,
# e a suspeita é que tenha travado a máquina em 2026-11-05. Este arquivo documenta o conteúdo
# da imagem physical-ai:jazzy, que foi montada com "docker run --memory=2g" e "docker commit".
FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-turtlebot4-simulator \
        ros-jazzy-turtlebot4-navigation \
        ros-jazzy-turtlebot4-desktop \
        ros-jazzy-irobot-create-nodes \
        ros-jazzy-nav2-loopback-sim \
        ros-jazzy-nav2-bringup \
        ros-jazzy-nav2-minimal-tb4-sim \
        ros-jazzy-nav2-simple-commander \
        ros-jazzy-turtlesim \
        ros-jazzy-demo-nodes-py \
        ros-dev-tools git python3-pytest \
        mesa-utils x11-apps xvfb \
    && rm -rf /var/lib/apt/lists/*

# Os tutoriais não têm pacote apt para Jazzy: compilamos do GitHub.
RUN bash -c "source /opt/ros/jazzy/setup.bash \
    && mkdir -p /opt/tb4_ws/src && cd /opt/tb4_ws/src \
    && git clone --depth 1 -b jazzy https://github.com/turtlebot/turtlebot4_tutorials.git \
    && cd /opt/tb4_ws \
    && colcon build --symlink-install --packages-select turtlebot4_python_tutorials turtlebot4_openai_tutorials"

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
    && echo "source /opt/tb4_ws/install/setup.bash" >> /root/.bashrc
CMD ["bash"]

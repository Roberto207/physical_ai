# Imagem única do projeto: ROS 2 Humble (o mesmo do robô) com o que o PC do lab roda.
# O entrypoint da imagem oficial já carrega o ROS. O repositório entra em /work por volume
# (scripts/env.sh), então mudar código não pede imagem nova.
#   docker build -t physical-ai docker/      (no PC do lab; o build não tem teto de memória)
FROM ros:humble-ros-base
ENV DEBIAN_FRONTEND=noninteractive
# turtlebot4_navigation: Nav2, AMCL, SLAM e o TurtleBot4Navigator. turtlebot4_desktop: RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-turtlebot4-navigation \
        ros-humble-turtlebot4-desktop \
        ros-humble-nav2-bringup \
        ros-humble-nav2-simple-commander \
        ros-humble-slam-toolbox \
        ros-humble-irobot-create-msgs \
        ros-humble-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

#!/usr/bin/env bash
# Um comando ROS avulso na rede do robô (só leitura, se você não publicar nada). Sem argumentos: bash.
#   ROBO=robot3 scripts/ros.sh ros2 topic list
# ROS_SUPER_CLIENT: no Discovery Server, só um super client enxerga os tópicos de todos.
set -euo pipefail
source "$(dirname "$0")/env.sh"
tty=(); [ -t 0 ] && tty=(-t)   # sem terminal (ex.: um agente rodando o comando), sem -t
exec "${ROS[@]}" -i "${tty[@]}" -e ROS_SUPER_CLIENT=True "$IMAGEM" "${@:-bash}"

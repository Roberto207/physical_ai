#!/usr/bin/env bash
# Mapa novo com SLAM. Não move o robô: dirija com scripts/teleop.sh em outro terminal.
#   scripts/mapa.sh                 sobe o SLAM e o RViz
#   scripts/mapa.sh salvar <nome>   grava mapas/<nome>.yaml e .pgm
set -euo pipefail
source "$(dirname "$0")/env.sh"
if [ "${1:-}" = salvar ]; then
  nome=${2:?"uso: scripts/mapa.sh salvar <nome>"}
  [[ "$nome" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Nome inválido"; exit 1; }
  [ ! -e "$REPO/mapas/$nome.yaml" ] || { echo "mapas/$nome.yaml já existe"; exit 1; }
  # map_saver_cli direto e com o tópico remapeado: o serviço save_map do slam_toolbox falha
  # com namespace (result=255, medido em 2026-11-19). O /map é transient_local.
  "${ROS[@]}" "$IMAGEM" bash -c "ros2 run nav2_map_server map_saver_cli -f /work/mapas/$nome \
    --ros-args -r map:=$NS/map -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0 \
    && chown $(id -u):$(id -g) /work/mapas/$nome.*"
  exit 0
fi
docker rm -f tb_slam tb_rviz >/dev/null 2>&1 || true
"${ROS[@]}" -d --name tb_slam --memory 2g "$IMAGEM" \
  ros2 launch turtlebot4_navigation slam.launch.py sync:=true namespace:="$NS"
xhost +SI:localuser:root >/dev/null
"${ROS[@]}" -d --name tb_rviz --memory 1g "$IMAGEM" \
  ros2 launch turtlebot4_viz view_robot.launch.py namespace:="$NS"
echo "SLAM no ar. Dirija com scripts/teleop.sh; ao terminar: scripts/mapa.sh salvar <nome>"

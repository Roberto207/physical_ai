#!/usr/bin/env bash
# Localização (AMCL no mapa salvo) e Nav2 do robô escolhido; com "rviz", também o RViz.
# Não move o robô. Depois: 2D Pose Estimate no RViz, na pose real da doca.
#   ROBO=robot3 scripts/subir.sh rviz        MAPA=/work/mapas/<outro>.yaml para outro mapa
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ -f "$REPO/${MAPA#/work/}" ] || { echo "Mapa não existe: $MAPA"; exit 1; }
docker rm -f tb_localizacao tb_nav2 tb_rviz >/dev/null 2>&1 || true
"${ROS[@]}" -d --name tb_localizacao --memory 1g "$IMAGEM" \
  ros2 launch /work/launch/localizacao.launch.py namespace:="$NS" map:="$MAPA" \
  params:=/work/config/localizacao.yaml
"${ROS[@]}" -d --name tb_nav2 --memory 2g "$IMAGEM" \
  ros2 launch /work/launch/nav2.launch.py namespace:="$NS" params_file:=/work/config/nav2.yaml
if [ "${1:-}" = rviz ]; then
  xhost +SI:localuser:root >/dev/null   # o contêiner roda como root
  "${ROS[@]}" -d --name tb_rviz --memory 1g "$IMAGEM" \
    ros2 launch turtlebot4_viz view_robot.launch.py namespace:="$NS"
fi
echo "Subiu para $ROBO. Logs: docker logs -f tb_nav2. Pronto quando aparecer 'Managed nodes are active'."
echo "Próximo: 2D Pose Estimate no RViz na pose real da doca."

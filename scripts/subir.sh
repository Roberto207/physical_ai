#!/usr/bin/env bash
# Sobe os serviços do robô escolhido em duas etapas (a ordem que funcionou no robô em 25/11).
# Não move o robô.
#   ROBO=robot3 scripts/subir.sh        localização (AMCL no mapa) + RViz
#        → espere "Managed nodes are active" (docker logs tb_localizacao) e faça o
#          2D Pose Estimate no RViz, na pose real da doca, com o laser sobre as paredes
#   ROBO=robot3 scripts/subir.sh nav2   Nav2 (espere "Managed nodes are active" em tb_nav2)
# MAPA=/work/mapas/<outro>.yaml usa outro mapa.
set -euo pipefail
source "$(dirname "$0")/env.sh"
if [ "${1:-}" = nav2 ]; then
  rodando tb_localizacao || { echo "Suba antes a localização: scripts/subir.sh"; exit 2; }
  docker rm -f tb_nav2 >/dev/null 2>&1 || true
  "${ROS[@]}" -d --name tb_nav2 --memory 2g "$IMAGEM" \
    ros2 launch /work/launch/nav2.launch.py namespace:="$NS" params_file:=/work/config/nav2.yaml
  echo "Nav2 subindo para $ROBO: docker logs -f tb_nav2"
  exit 0
fi
[ -f "$REPO/${MAPA#/work/}" ] || { echo "Mapa não existe: $MAPA"; exit 1; }
docker rm -f tb_localizacao tb_nav2 tb_rviz >/dev/null 2>&1 || true
"${ROS[@]}" -d --name tb_localizacao --memory 1g "$IMAGEM" \
  ros2 launch /work/launch/localizacao.launch.py namespace:="$NS" map:="$MAPA" \
  params:=/work/config/localizacao.yaml
xhost +SI:localuser:root >/dev/null   # o contêiner roda como root
"${ROS[@]}" -d --name tb_rviz --memory 1g "$IMAGEM" \
  ros2 launch turtlebot4_viz view_robot.launch.py namespace:="$NS"
echo "Localização e RViz subindo para $ROBO: docker logs -f tb_localizacao"
echo "Depois do 2D Pose Estimate: scripts/subir.sh nav2"

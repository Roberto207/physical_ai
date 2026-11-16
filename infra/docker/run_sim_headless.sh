#!/usr/bin/env bash
# Sobe a simulação do TurtleBot 4 (Gazebo, mundo vazio) SEM janela, com limites de segurança.
# Uso: ./run_sim_headless.sh        (Ctrl+C ou "docker rm -f tb4sim" para parar)
# Limites: 2,5 GiB de RAM (sem swap) e 4 CPUs. Se estourar, só o container morre.
set -euo pipefail
cd "$(dirname "$0")"

docker rm -f tb4sim >/dev/null 2>&1 || true
docker run -d --name tb4sim --init \
  --memory=2500m --memory-swap=2500m --cpus=4 --device /dev/dri \
  -v "$PWD/sim_headless.launch.py:/opt/ros/jazzy/share/turtlebot4_gz_bringup/launch/sim.launch.py:ro" \
  physical-ai:jazzy bash -c '
    Xvfb :99 -screen 0 1280x720x24 -nolisten tcp & sleep 2
    export DISPLAY=:99
    source /opt/ros/jazzy/setup.bash
    ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py \
      world:=empty rviz:=false slam:=false localization:=false nav2:=false'

echo "Rodando. Ver log: docker logs -f tb4sim | Entrar: docker exec -it tb4sim bash"

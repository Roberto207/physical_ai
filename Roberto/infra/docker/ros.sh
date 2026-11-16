#!/usr/bin/env bash
# Terminal ROS 2 Jazzy para estudar, com janelas (turtlesim, RViz) na sua tela.
#
#   ./ros.sh          abre um terminal. Rode de novo em outra aba para ter mais terminais
#   ./ros.sh parar    desliga o container e devolve a pasta workspace/ para o seu usuário
#
# A pasta workspace/ do projeto aparece em /workspace: o que estiver lá não some.
# O resto do container é descartável. Limites: 2 GiB de RAM (sem swap) e 3 CPUs.
set -euo pipefail
cd "$(dirname "$0")/../.."
NOME=tb4ros

case "${1:-}" in
  parar)
    docker exec "$NOME" chown -R "$(id -u):$(id -g)" /workspace 2>/dev/null || true
    docker rm -f "$NOME" >/dev/null 2>&1 || true
    xhost -SI:localuser:root >/dev/null 2>&1 || true
    echo "Parado."
    ;;
  "")
    mkdir -p workspace
    if [ "$(docker inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" != "true" ]; then
      docker rm -f "$NOME" >/dev/null 2>&1 || true
      xhost +SI:localuser:root >/dev/null
      docker run -d --name "$NOME" --init --memory=2g --memory-swap=2g --cpus=3 \
        --device /dev/dri -e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
        -v "$PWD/workspace:/workspace" physical-ai:jazzy sleep infinity >/dev/null
    fi
    docker exec -it "$NOME" bash -c \
      "source /opt/ros/jazzy/setup.bash; source /opt/tb4_ws/install/setup.bash; cd /workspace; exec bash"
    ;;
  *)
    sed -n 2,8p "$0"
    ;;
esac

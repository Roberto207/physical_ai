#!/usr/bin/env bash
# Treino sem Gazebo: Nav2 + simulador leve (nav2_loopback_sim) + base e bateria falsas. --> Patrol_control testes 
#
#   ./treino_leve.sh iniciar [--rviz] [--patrulha]   sobe tudo em segundo plano
#   ./treino_leve.sh terminal                        abre um terminal ROS dentro do container
#   ./treino_leve.sh logs                            mostra o que a patrulha está dizendo
#   ./treino_leve.sh parar                           desliga tudo e libera a memória
#
# A pasta workspace/ do projeto aparece em /workspace, e infra/tools/ em /tools.
# Limites: 2 GiB de RAM (sem swap) e 3 CPUs. Se estourar, só o container morre.
# Variáveis opcionais: BATERIA_INICIAL (0.5), DESCARGA (0.002 por s), CARGA (0.05 por s), MAPA.
set -euo pipefail
cd "$(dirname "$0")/.."
NOME=tb4lite

case "${1:-}" in
  iniciar)
    shift
    USAR_RVIZ=False; PATRULHA=""; X11=()
    for arg in "$@"; do
      case "$arg" in
        --rviz) USAR_RVIZ=True ;;
        --patrulha) PATRULHA="ros2 run turtlebot4_python_tutorials patrol_loop > /tmp/patrol.log 2>&1 &" ;;
        *) echo "opção desconhecida: $arg"; exit 1 ;;
      esac
    done
    if [ "$USAR_RVIZ" = True ]; then
      xhost +SI:localuser:root >/dev/null
      X11=(-e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix:ro --device /dev/dri)
    fi
    mkdir -p ../workspace
    MAPA="${MAPA:-/opt/ros/jazzy/share/turtlebot4_navigation/maps/warehouse.yaml}"
    docker rm -f "$NOME" >/dev/null 2>&1 || true
    docker run -d --name "$NOME" --init --memory=2g --memory-swap=2g --cpus=3 \
      -v "$PWD/tools:/tools:ro" -v "$PWD/../workspace:/workspace" ${X11[@]+"${X11[@]}"} \
      physical-ai:jazzy bash -c "
        source /opt/ros/jazzy/setup.bash; source /opt/tb4_ws/install/setup.bash
        ros2 launch nav2_bringup tb4_loopback_simulation.launch.py use_rviz:=$USAR_RVIZ map:=$MAPA > /tmp/nav.log 2>&1 &
        sleep 15
        python3 /tools/fake_tb4_base.py --ros-args \
          -p battery_start:=${BATERIA_INICIAL:-0.5} -p drain_per_s:=${DESCARGA:-0.002} -p charge_per_s:=${CARGA:-0.05} > /tmp/fake.log 2>&1 &
        sleep 5
        $PATRULHA
        wait" >/dev/null
    echo "Subindo (cerca de 20 s). Depois: ./treino_leve.sh logs ou ./treino_leve.sh terminal"
    ;;
  terminal)
    docker exec -it "$NOME" bash -c "source /opt/ros/jazzy/setup.bash; source /opt/tb4_ws/install/setup.bash; cd /workspace; exec bash"
    ;;
  logs)
    docker exec "$NOME" bash -c "grep -vE 'aiting|Setting initial|Publishing Initial|Estimated|Distance remaining' /tmp/patrol.log | tail -30"
    ;;
  parar)
    docker exec "$NOME" chown -R "$(id -u):$(id -g)" /workspace 2>/dev/null || true
    docker rm -f "$NOME" >/dev/null 2>&1 || true
    xhost -SI:localuser:root >/dev/null 2>&1 || true
    echo "Parado."
    ;;
  *)
    sed -n 2,11p "$0"
    ;;
esac

# shellcheck shell=bash
# Robô escolhido e "docker run" comum. Os outros scripts fazem "source" deste.
#   ROBO=robot3 scripts/subir.sh        (padrão: robot1)
# Valores lidos do /etc/turtlebot4/setup.bash de cada robô. O IP vem do DHCP: se mudar, ajuste.
# A posição do IP em ROS_DISCOVERY_SERVER é o id do servidor (";IP:11811;" = id 1).
# https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ROBO=${ROBO:-robot1}
case "$ROBO" in
  robot1) IP=192.168.7.7;   DS=";$IP:11811;" ;;     # Wi-Fi PixelLab-2.4GHz, id 1
  robot3) IP=192.168.68.53; DS=";;;$IP:11811;" ;;   # Wi-Fi Robotica_Deco, id 3
  *) echo "ROBO desconhecido: '$ROBO' (robot1 ou robot3)" >&2; exit 1 ;;
esac
NS=/$ROBO                                  # o ROBOT_NAMESPACE do robô
MAPA=${MAPA:-/work/mapas/mapa_lab_novo.yaml}
IMAGEM=physical-ai
# --network host: o DDS precisa achar o robô no Wi-Fi. --ipc host: o FastDDS usa memória
# compartilhada entre os contêineres. --init repassa Ctrl+C e "docker stop" ao programa.
# UDPv4: evita as portas SHM com erro open_and_lock_file. O rótulo deixa o parar.sh achar tudo.
ROS=(docker run --rm --init --network host --ipc host -l tb4.robo="$ROBO"
     -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp -e FASTDDS_BUILTIN_TRANSPORTS=UDPv4
     -e ROS_DOMAIN_ID=0 -e ROS_DISCOVERY_SERVER="$DS"
     -e DISPLAY="${DISPLAY:-}" -v /tmp/.X11-unix:/tmp/.X11-unix:ro
     -v "$REPO":/work -w /work)

rodando() { [ -n "$(docker ps -q -f "name=^$1\$")" ]; }

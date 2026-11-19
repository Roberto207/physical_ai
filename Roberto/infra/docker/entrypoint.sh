#!/usr/bin/env bash
# Entrypoint de todas as imagens do projeto (Dockerfile). Roda DENTRO do container.
#
# 1. Carrega o ROS da distro da imagem. ROS_DISTRO vem da imagem oficial ros:<distro>-ros-base,
#    então nada aqui (nem nos compose) escreve o nome da distro (IMG-03, IMG-04).
# 2. Carrega o overlay dos tutoriais (/opt/tb4_ws), se a imagem tiver.
# 3. Se COMPILAR_WS tiver uma lista de pacotes (separados por vírgula), compila esses pacotes de
#    /workspace/meu_ws/src em /tmp e carrega o resultado. Em /tmp, e não no workspace, para o
#    container não deixar arquivos de root na pasta do projeto. Leva poucos segundos.
# 4. Executa o comando do serviço.
set -e
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO:?a imagem não define ROS_DISTRO}/setup.bash"
if [ -f /opt/tb4_ws/install/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/tb4_ws/install/setup.bash
fi

if [ -n "${COMPILAR_WS:-}" ]; then
  if ! colcon build --base-paths /workspace/meu_ws/src --packages-select ${COMPILAR_WS//,/ } \
         --build-base /tmp/build --install-base /tmp/install > /tmp/colcon.log 2>&1; then
    cat /tmp/colcon.log
    echo "O colcon build de '${COMPILAR_WS}' falhou (log acima)." >&2
    exit 1
  fi
  # shellcheck disable=SC1091
  source /tmp/install/setup.bash
fi

exec "$@"

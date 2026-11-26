#!/usr/bin/env bash
# Patrulha no robô real. MOVE O ROBÔ. Antes: scripts/subir.sh rviz e 2D Pose Estimate na doca.
#   ROBO=robot3 scripts/patrulha.sh voltas 1 | ida-e-volta | continuo | doca
#   scripts/patrulha.sh --verificar-localizacao voltas 1      (confere tudo sem mover)
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ $# -gt 0 ] || { sed -n 2,4p "$0"; exit 2; }
rodando tb_nav2 && rodando tb_localizacao || { echo "Suba antes: scripts/subir.sh rviz"; exit 2; }
# Um controlador por vez: o LLM também comanda o robô.
! rodando tb_llm || { echo "O LLM está rodando e também comanda o robô: encerre-o antes."; exit 2; }
echo "ROBÔ: $ROBO. Ctrl+C cancela a meta; não garante a volta à doca."
exec "${ROS[@]}" -it --name tb_patrulha --memory 512m "$IMAGEM" \
  python3 patrulha.py "$@" --ros-args -r __ns:="$NS"

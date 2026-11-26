#!/usr/bin/env bash
# Dirigir pelo teclado. MOVE O ROBÔ. Robô fora da doca e pessoa ao lado.
# stamped:=false: o robô Humble só aceita Twist sem carimbo. 0,15 m/s para mapear com gente perto.
set -euo pipefail
source "$(dirname "$0")/env.sh"
exec "${ROS[@]}" -it --name tb_teleop "$IMAGEM" \
  ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r __ns:="$NS" \
  -p stamped:=false -p speed:=0.15 -p turn:=0.5

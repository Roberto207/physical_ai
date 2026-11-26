#!/usr/bin/env bash
# Terminal de pedidos ao LLM. Cada linha é um pedido; só Enter envia "pare".
#   ROBO=robot3 scripts/falar.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"
# "stty iutf8": sem ele o Backspace apaga um byte, e não a letra acentuada inteira.
exec "${ROS[@]}" -it --name tb_falar "$IMAGEM" \
  bash -c "stty iutf8 2>/dev/null; exec python3 llm/falar.py --ros-args -r __ns:=$NS"

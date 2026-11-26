#!/usr/bin/env bash
# Comandos em linguagem natural (Ollama no PC). Os pedidos saem do scripts/falar.sh.
#   scripts/llm.sh          freio ligado: interpreta e registra, NÃO move
#   scripts/llm.sh mover    O ROBÔ SE MOVE a cada pedido aceito (Nav2 no ar e 2D Pose Estimate antes)
set -euo pipefail
source "$(dirname "$0")/env.sh"
FREIO=true
[ "${1:-}" != mover ] || FREIO=false
curl -sf http://127.0.0.1:11434/api/tags >/dev/null || {
  echo "Ollama não responde em 127.0.0.1:11434. No PC: ollama serve; ollama pull qwen2.5:1.5b"; exit 2; }
if [ "$FREIO" = false ]; then
  rodando tb_nav2 || { echo "Suba antes: scripts/subir.sh e scripts/subir.sh nav2"; exit 2; }
  ! rodando tb_patrulha || { echo "A patrulha está rodando: encerre-a antes."; exit 2; }
  echo "ROBÔ: $ROBO. FREIO DESLIGADO: o robô anda a cada pedido. Pessoa ao lado; Enter vazio no falar.sh = pare."
fi
exec "${ROS[@]}" -it --name tb_llm --memory 512m "$IMAGEM" \
  python3 llm/no_llm.py --ros-args -r __ns:="$NS" -p freio:=$FREIO

#!/usr/bin/env bash
# Só leitura: o robô responde e os tópicos dele chegam ao PC? Não move nada.
#   ROBO=robot3 scripts/checar.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"
echo "ROBÔ: $ROBO ($IP, namespace $NS)"
ping -c 2 -W 2 "$IP" >/dev/null && echo "  ok   ping $IP" || { echo "REPROVADO: $IP não responde"; exit 2; }
# O DDS do robô anuncia também 192.168.185.x (cabo) e 192.168.186.x (USB da Create 3). Sem rota
# por ele, a descoberta não fecha (medido em 2026-11-16). Hipótese H1 da task 2: no Humble com o
# create3_republisher a rota não seria mais necessária; até confirmar, ela continua exigida.
for alvo in 192.168.186.2 192.168.185.3; do
  if ip route get "$alvo" | grep -q " via " && ! ip route get "$alvo" | grep -q " via $IP "; then
    echo "  aviso: sem rota para ${alvo%.*}.0/24 pelo robô. Na conexão Wi-Fi em uso:"
    echo "    sudo nmcli connection modify <conexão> +ipv4.routes \"${alvo%.*}.0/24 $IP 500\""
  fi
done
# ROS_SUPER_CLIENT: no Discovery Server, só um super client lista os tópicos de todos.
topicos=$("${ROS[@]}" -e ROS_SUPER_CLIENT=True "$IMAGEM" \
  bash -c 'for i in 1 2 3; do ros2 topic list; sleep 3; done | sort -u')
falta=0
for t in scan tf odom battery_state dock_status; do
  if grep -qx "$NS/$t" <<<"$topicos"; then echo "  ok   $NS/$t"; else echo "  FALTA $NS/$t"; falta=1; fi
done
for c in tb_localizacao tb_nav2 tb_rviz tb_llm tb_patrulha; do
  rodando "$c" && echo "  no ar: $c"
done
[ "$falta" = 0 ] && echo "APROVADO" || { echo "REPROVADO: confira o Wi-Fi, o namespace e as rotas acima"; exit 2; }

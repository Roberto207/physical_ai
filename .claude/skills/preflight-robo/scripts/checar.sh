#!/usr/bin/env bash
# Leituras do preflight da patrulha oficial (specs/preflight-robo/SPEC.md, seção 5).
# SÓ LÊ: não sobe, não para nem recria serviço, e não envia nada ao robô.
#
#   checar.sh A  [relatorio.md]   antes de subir os serviços (A1 a A8)
#   checar.sh C  [relatorio.md]   estabilidade dos nós (C1 a C3; leva mais de 1 minuto)
#   checar.sh C4 [relatorio.md]   verificação do programa de patrulha, sem movimento
#
# Sai com 0 se tudo passou, 1 se algum item foi reprovado ou não pôde ser verificado, 2 em uso
# errado. ROBO_IP troca só o endereço do ping (para testar o caso "robô desligado").
set -uo pipefail
cd "$(git -C "$(dirname "$(readlink -f "$0")")" rev-parse --show-toplevel)" || exit 2

FASE=${1:-}
case "$FASE" in A|C|C4) ;; *) sed -n 2,11p "$0"; exit 2 ;; esac
REL=${2:-workspace/logs/preflight_$(date +%F_%H-%M-%S).md}
mkdir -p "$(dirname "$REL")"
LAB=infra/docker/lab.sh
NS=/robot1
NOS="map_server amcl controller_server smoother_server planner_server behavior_server
     bt_navigator waypoint_follower velocity_smoother"
RUINS=0

# resultado <item> <PASSOU|REPROVOU|NÃO VERIFICADO|OPERADOR> <resumo> [saída completa]
resultado() {
  printf '%-3s | %-14s | %s\n' "$1" "$2" "$3"
  { printf '\n## %s: %s (%s)\n\n%s\n' "$1" "$2" "$(date +%T)" "$3"
    [ -n "${4:-}" ] && printf '\n```text\n%s\n```\n' "$4"; } >> "$REL"
  case "$2" in REPROVOU|'NÃO VERIFICADO') RUINS=$((RUINS + 1)) ;; esac
}

# Comando ROS num contêiner temporário. O primeiro número é o prazo total, no PC.
ferr() { local prazo=$1; shift; timeout "$prazo" "$LAB" robo compose run --rm -T ferramentas "$@" 2>&1; }

fase_a() {
  local img out ruim='' ip sim extras val

  for img in base robo; do
    out=$(timeout 60 docker run --rm --network none "physical-ai:$img" printenv ROS_DISTRO 2>&1)
    [ "$out" = humble ] || ruim+="physical-ai:$img=${out:-sem resposta} "
  done
  if [ -z "$ruim" ]; then resultado A1 PASSOU 'imagens base e robo são humble'
  else resultado A1 REPROVOU "$ruim"; fi

  if sim=$(timeout 60 "$LAB" sim estado 2>/dev/null) &&
     out=$(docker ps --no-trunc --format '{{.Label "com.docker.compose.service"}}|{{.Names}}|{{.Command}}'); then
    sim=$(tail -n +2 <<<"$sim")
    extras=$(grep -E '^(slam|teleop|patrulha)\||patrol_loop|loop\.py' <<<"$out")
    if [ -z "$sim$extras" ]; then resultado A2 PASSOU 'nada concorrendo' "$out"
    else resultado A2 REPROVOU 'há serviço do simulador, mapeamento, controle manual ou patrulha rodando' "$sim
$extras"; fi
  else resultado A2 'NÃO VERIFICADO' 'o Docker não respondeu'; fi

  out=$(timeout 60 "$LAB" conferir workspace/mapas/mapa_lab_novo.yaml 2>&1)
  if grep -q '^UTILIZÁVEL' <<<"$out"; then resultado A3 PASSOU 'mapa_lab_novo UTILIZÁVEL' "$out"
  else resultado A3 REPROVOU 'o mapa não foi aprovado' "$out"; fi

  ip=${ROBO_IP:-$(sed -nE 's/^ROS_DISCOVERY_SERVER=;*([0-9.]+):.*/\1/p' infra/lab/rede_lab.env)}
  out=$(LC_ALL=C timeout 30 ping -c 5 -W 2 "$ip" 2>&1)
  if grep -q ' 0% packet loss' <<<"$out"; then
    resultado A4 PASSOU "$ip sem perda; $(grep '^rtt' <<<"$out")" "$out"
  else
    resultado A4 REPROVOU "$ip: $(grep -o '[0-9.]*% packet loss' <<<"$out" || echo sem resposta)" "$out"
    for val in A5 A6 A7; do resultado "$val" 'NÃO VERIFICADO' 'o robô não respondeu em A4'; done
    fase_a8; return
  fi

  out=$(timeout 150 "$LAB" robo checar-rede 2>&1)
  if grep -q 'REDE OK' <<<"$out" && ! grep -q 'aviso:' <<<"$out"; then
    resultado A5 PASSOU 'REDE OK, com bateria e doca' "$out"
  else resultado A5 REPROVOU 'rede reprovada ou com aviso' "$out"; fi

  out=$(ferr 90 timeout 30 ros2 topic echo "$NS/dock_status" irobot_create_msgs/msg/DockStatus \
        --qos-profile sensor_data --once)
  if grep -q '^is_docked: true' <<<"$out"; then resultado A6 PASSOU 'is_docked: true' "$out"
  elif grep -q '^is_docked: false' <<<"$out"; then resultado A6 REPROVOU 'o robô está fora da doca' "$out"
  else resultado A6 'NÃO VERIFICADO' 'sem leitura da doca no prazo' "$out"; fi

  out=$(ferr 90 timeout 30 ros2 topic echo "$NS/battery_state" sensor_msgs/msg/BatteryState \
        --qos-profile sensor_data --once --field percentage)
  val=$(grep -m1 -E '^([0-9]+(\.[0-9]+)?|\.?nan)$' <<<"$out")
  if [ -z "$val" ] || [[ "$val" == *nan ]]; then
    resultado A7 'NÃO VERIFICADO' "bateria sem valor medido (${val:-sem leitura})" "$out"
  elif awk -v v="$val" 'BEGIN { exit !(v >= 0.20) }'; then
    resultado A7 PASSOU "bateria $val" "$out"
  else resultado A7 REPROVOU "bateria $val, abaixo de 0.20" "$out"; fi

  fase_a8
}

fase_a8() {
  local out
  if out=$(python3 -I - workspace/patrulha_oficial/patrol_loop.py <<'PY'
import ast, sys
nos = ast.parse(open(sys.argv[1], encoding='utf-8').read()).body
v = {n.targets[0].id: n.value for n in nos
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
print('DOCA   ', ast.literal_eval(v['DOCA']))
for i, p in enumerate(ast.literal_eval(v['PONTOS']), 1):
    print('ponto', i, p)
PY
  ); then
    resultado A8 OPERADOR 'o operador precisa confirmar as coordenadas' "$out"
    echo "$out"
  else resultado A8 'NÃO VERIFICADO' 'não li as coordenadas' "$out"; fi
}

estados() {   # estados <item>
  local out no ruim=''
  out=$(ferr 240 bash -c "for n in $(echo $NOS); do echo \"== \$n\";
        timeout 15 ros2 service call $NS/\$n/get_state lifecycle_msgs/srv/GetState 2>&1 | tail -n 2; done")
  for no in $NOS; do
    awk -v n="== $no" '$0 == n {v = 1; next} /^== / {v = 0} v' <<<"$out" |
      grep -q "label='active'" || ruim+="$no "
  done
  if [ -z "$ruim" ]; then resultado "$1" PASSOU 'todos os nós active' "$out"
  else resultado "$1" REPROVOU "sem confirmação de active: $ruim" "$out"; fi
}

fase_c() {
  local out ruins
  estados C1
  echo 'aguardando 60 s antes de repetir...'
  sleep 60
  estados C2
  if [ -z "$("$LAB" robo compose ps -q nav2 2>/dev/null)" ] ||
     [ -z "$("$LAB" robo compose ps -q localizacao 2>/dev/null)" ]; then
    resultado C3 'NÃO VERIFICADO' 'nav2 ou localizacao não está rodando'
    return
  fi
  out=$(timeout 60 "$LAB" robo compose logs --no-color nav2 localizacao 2>&1)
  ruins=$(grep -E 'CRITICAL FAILURE|Failed to bring up|no map received' <<<"$out")
  if [ -z "$ruins" ]; then resultado C3 PASSOU 'logs sem falha desde a subida'
  else resultado C3 REPROVOU "$(wc -l <<<"$ruins") linha(s) de falha nos logs" "$(tail -n 15 <<<"$ruins")"; fi
}

fase_c4() {
  local out rc
  out=$(ferr 180 timeout 120 python3 /workspace/patrulha_oficial/patrol_loop.py \
        --verificar-localizacao --ros-args -r "__ns:=$NS")
  rc=$?
  case $rc in
    0) resultado C4 PASSOU 'localização e ações verificadas, sem movimento' "$out" ;;
    2) resultado C4 REPROVOU 'código 2: robô não confirmado na doca' "$out" ;;
    7) resultado C4 REPROVOU 'código 7: sem map→odom recente (refazer o 2D Pose Estimate)' "$out" ;;
    8) resultado C4 REPROVOU 'código 8: ação de navegação, dock ou saída da doca indisponível' "$out" ;;
    *) resultado C4 'NÃO VERIFICADO' "código $rc" "$out" ;;
  esac
}

[ -f "$REL" ] || printf '# Preflight da patrulha oficial, %s\n' "$(date '+%F %T')" > "$REL"
case "$FASE" in A) fase_a ;; C) fase_c ;; C4) fase_c4 ;; esac
echo "ITENS REPROVADOS OU NÃO VERIFICADOS NA FASE $FASE: $RUINS"
echo "RELATÓRIO: $REL"
[ "$RUINS" = 0 ]

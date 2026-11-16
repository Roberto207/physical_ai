#!/usr/bin/env bash
# Roda DENTRO do container, chamado pelo teste_l1.sh. Não rode à mão no notebook.
#
# Compila o pacote patrulha_tb4, sobe o que fica ao lado do nó (Nav2 leve e base falsa,
# conforme o cenário), roda a patrulha e para quando o cenário chega ao ponto esperado.
set -o pipefail   # sem -u: os setup.bash do ROS usam variáveis não definidas
SAIDA=/evidencias
trap 'chown -R "$DONO" /workspace/meu_ws "$SAIDA" 2>/dev/null' EXIT

source /opt/ros/jazzy/setup.bash
source /opt/tb4_ws/install/setup.bash

cd /workspace/meu_ws
if ! colcon build --packages-select patrulha_tb4 > "$SAIDA/build.log" 2>&1; then
  echo "O colcon build falhou. Veja build.log."
  exit 20
fi
source install/setup.bash

CONFIG_ARQ="$(ros2 pkg prefix patrulha_tb4)/share/patrulha_tb4/config/$CONFIG"
MAPA="$(python3 -c "from patrulha_tb4.config import carregar; print(carregar('$CONFIG_ARQ').mapa)")"
echo "config: $CONFIG_ARQ"
echo "mapa: $MAPA"

if [ "$CENARIO" = l1b ]; then
  # L1b (H4): o nav2.yaml oficial do TurtleBot 4, sem alterar o arquivo. Ele manda a
  # velocidade com carimbo de tempo (TwistStamped), e o simulador leve, por padrão, espera
  # sem carimbo: sem a chave abaixo, o robô simulado não sai do lugar (visto em 13/nov).
  { cat /opt/ros/jazzy/share/turtlebot4_navigation/config/nav2.yaml
    printf '\nloopback_simulator:\n  ros__parameters:\n    enable_stamped_cmd_vel: true\n'
  } > /tmp/nav2_l1b.yaml
fi

if [ "$SUBIR_NAV2" = 1 ]; then
  # O Nav2 do simulador leve às vezes desiste ao subir ("Aborting bringup": a transformada
  # do odom não fica pronta a tempo). Visto em 12 e 13/nov, com e sem carga no notebook.
  # Quando isso acontece, derruba e sobe de novo, até 3 vezes, e anota a tentativa.
  for TENTATIVA in 1 2 3; do
    # shellcheck disable=SC2086
    ros2 launch nav2_bringup tb4_loopback_simulation.launch.py use_rviz:=False map:="$MAPA" $NAV2_EXTRA \
      > "$SAIDA/nav2.log" 2>&1 &
    sleep 15
    grep -q "Aborting bringup" "$SAIDA/nav2.log" || break
    echo "Nav2 não subiu na tentativa $TENTATIVA (Aborting bringup)" | tee -a "$SAIDA/nav2_tentativas.txt"
    cp "$SAIDA/nav2.log" "$SAIDA/nav2_falhou_$TENTATIVA.log"
    pkill -TERM -f "nav2|loopback_simulator|robot_state_publisher|component_container|lifecycle_manager|map_server|static_transform"
    sleep 5
    pkill -KILL -f "nav2|loopback_simulator|robot_state_publisher|component_container|lifecycle_manager|map_server|static_transform"
    sleep 2
  done
fi
if [ "$SUBIR_BASE" = 1 ]; then
  # shellcheck disable=SC2086
  python3 /tools/fake_tb4_base.py --ros-args $BASE > "$SAIDA/base_falsa.log" 2>&1 &
  sleep 3
fi

# shellcheck disable=SC2086
ros2 launch patrulha_tb4 patrulha.launch.py config:="$CONFIG_ARQ" pasta_log:="$SAIDA" $PATRULHA_EXTRA \
  > "$SAIDA/patrulha.log" 2>&1 &
PATRULHA=$!

INICIO=$(date +%s)
MOTIVO="a patrulha encerrou sozinha"
while kill -0 "$PATRULHA" 2>/dev/null; do
  if [ $(( $(date +%s) - INICIO )) -gt "$LIMITE_S" ]; then
    MOTIVO="tempo esgotado ($LIMITE_S s)"
    break
  fi
  JSONL=$(ls "$SAIDA"/*.jsonl 2>/dev/null | head -1)
  if [ -n "$JSONL" ] && python3 /tools/conferir_l1.py "$CENARIO" "$JSONL" --pronto; then
    MOTIVO="o cenário chegou ao ponto esperado"
    break
  fi
  sleep 2
done

{
  echo "parada: $MOTIVO"
  if pgrep -x rviz2 >/dev/null; then echo "rviz2: RODANDO"; else echo "rviz2: nenhum processo (AMB-03)"; fi
  echo "nos: $(ros2 node list --no-daemon --spin-time 3 2>/dev/null | tr '\n' ' ')"
} > "$SAIDA/ambiente.txt"

if kill -0 "$PATRULHA" 2>/dev/null; then
  # PAT-15: o Ctrl+C precisa cancelar a ação, gravar o resumo e sair em até 3 s.
  # O sinal vai direto para o nó: um processo posto em segundo plano por um script
  # ignora o SIGINT, então mandar para o `ros2 launch` não chegaria a ele.
  date +%s.%N > "$SAIDA/sinal.txt"
  pkill -INT -f 'lib/patrulha_tb4/patrulha'
  for _ in $(seq 1 20); do
    kill -0 "$PATRULHA" 2>/dev/null || break
    sleep 0.5
  done
  kill -9 "$PATRULHA" 2>/dev/null
fi
wait "$PATRULHA" 2>/dev/null
exit 0

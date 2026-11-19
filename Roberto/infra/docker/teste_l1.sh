#!/usr/bin/env bash
# Teste L1 da spec specs/patrol-inf: o nosso nó patrulha_tb4 no simulador leve
# (Nav2 + nav2_loopback_sim vendorizado + base e bateria falsas), sem RViz, um cenário por vez.
#
#   ./teste_l1.sh <cenario>      roda o cenário, guarda a evidência e dá o veredito
#   ./teste_l1.sh lista          mostra os cenários
#   ./teste_l1.sh parar          desliga o container, se tiver ficado algum
#
# Cada execução deixa uma pasta em workspace/logs/l1/<data>-<cenario>/ com o log JSONL
# da patrulha, os logs do Nav2, da base falsa e da patrulha, o pico de RAM e o veredito (SIM-05).
#
# Este script só faz o que é do host: o container, a pasta de evidências, a memória, as
# tentativas e o veredito. O que sobe DENTRO do container é o lab_tb4/launch/l1.launch.py, e os
# parâmetros de cada cenário estão em lab_tb4/config/cenarios_l1.yaml (SIM-04b).
#
# Segurança da máquina (TST-06): o teste NÃO sobe se a memória disponível for menor que
# o teto do container (TETO_MB, padrão 2048) mais 1 GiB de folga. Se estourar o teto,
# só o container morre.
set -euo pipefail
ESTE=$(readlink -f "$0")   # antes do cd: o $0 pode ser relativo
cd "$(dirname "$ESTE")/.."
RAIZ="$(cd .. && pwd)"
NOME=tb4l1
IMAGEM=physical-ai:sim
TETO_MB="${TETO_MB:-2048}"
FOLGA_MB=1024
TENTATIVAS=3          # SIM-06: o Nav2 leve às vezes não sobe ("Aborting bringup")
LAB="$RAIZ/workspace/meu_ws/src/lab_tb4"
CENARIOS_YAML="$LAB/config/cenarios_l1.yaml"
CONFERIR="$LAB/lab_tb4/conferir_l1.py"

cenarios() { python3 "$LAB/lab_tb4/cenarios.py" "$CENARIOS_YAML" "$@"; }

CENARIO="${1:-}"
case "$CENARIO" in
  parar)
    docker rm -f "$NOME" >/dev/null 2>&1 || true
    echo "Parado."; exit 0 ;;
  ''|lista|-h|--help)
    sed -n 2,18p "$ESTE"
    echo "Cenários: $(cenarios nomes | tr '\n' ' ')"
    exit 0 ;;
esac
# SIM-04: nome desconhecido lista os cenários e sai, sem container.
if ! cenarios tem "$CENARIO"; then
  echo "Cenário desconhecido: $CENARIO"
  echo "Cenários: $(cenarios nomes | tr '\n' ' ')"
  exit 0
fi

# TST-06: recusa subir sem folga de memória.
LIVRE_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$LIVRE_MB" -lt $((TETO_MB + FOLGA_MB)) ]; then
  echo "RECUSADO (TST-06): há $LIVRE_MB MiB disponíveis; preciso de $((TETO_MB + FOLGA_MB)) MiB"
  echo "(teto de $TETO_MB MiB + folga de $FOLGA_MB MiB). Feche o navegador e os programas pesados."
  exit 3
fi

PASTA="$RAIZ/workspace/logs/l1/$(date +%Y-%m-%d_%H-%M-%S)-$CENARIO"
mkdir -p "$PASTA"
echo "Cenário: $CENARIO | memória disponível: $LIVRE_MB MiB | teto: $TETO_MB MiB"
echo "Evidências: $PASTA"

# Se o usuário apertar Ctrl+C, o container não fica para trás.
trap 'docker rm -f "$NOME" >/dev/null 2>&1 || true' EXIT
echo "hora,memoria" > "$PASTA/docker_stats.csv"

rodar_container() {
  docker rm -f "$NOME" >/dev/null 2>&1 || true
  # Roda com o usuário do host: o que o container grava em /evidencias e /workspace já nasce
  # dele (antes, um chown no fim). HOME=/tmp porque esse usuário não existe na imagem.
  # O entrypoint compila os três pacotes em /tmp (COMPILAR_WS) antes do launch.
  docker run -d --name "$NOME" --init --memory="${TETO_MB}m" --memory-swap="${TETO_MB}m" --cpus=3 \
    --user "$(id -u):$(id -g)" -e HOME=/tmp -e ROS_LOG_DIR=/evidencias/ros_log \
    -e COMPILAR_WS=patrulha_tb4,lab_tb4,nav2_loopback_sim \
    -v "$RAIZ/workspace:/workspace" -v "$PASTA:/evidencias" \
    "$IMAGEM" ros2 launch lab_tb4 l1.launch.py cenario:="$CENARIO" pasta:=/evidencias >/dev/null

  # Amostra a RAM do container a cada 5 s, até ele terminar.
  while [ "$(docker inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" = "true" ]; do
    USO=$(docker stats --no-stream --format '{{.MemUsage}}' "$NOME" 2>/dev/null | cut -d/ -f1 | tr -d ' ')
    [ -n "$USO" ] && echo "$(date +%H:%M:%S),$USO" >> "$PASTA/docker_stats.csv"
    sleep 5
  done
  MORTO_POR_MEMORIA=$(docker inspect -f '{{.State.OOMKilled}}' "$NOME" 2>/dev/null || echo "?")
  docker logs "$NOME" > "$PASTA/container.log" 2>&1 || true
  docker rm -f "$NOME" >/dev/null 2>&1 || true
}

TENTATIVA=1
NAV2_NAO_SUBIU=0
while :; do
  rodar_container
  [ -f "$PASTA/nav2_abortou" ] || break
  # SIM-06: o vigia_l1 viu "Aborting bringup" e parou o cenário antes da patrulha subir.
  echo "tentativa $TENTATIVA: Aborting bringup" | tee -a "$PASTA/nav2_tentativas.txt"
  mv "$PASTA/nav2_abortou" "$PASTA/nav2_abortou_$TENTATIVA"
  cp "$PASTA/container.log" "$PASTA/container_tentativa_$TENTATIVA.log"
  if [ "$TENTATIVA" -ge "$TENTATIVAS" ]; then NAV2_NAO_SUBIU=1; break; fi
  TENTATIVA=$((TENTATIVA + 1))
done
trap - EXIT

# Os logs de cada parte, separados do container.log pelo prefixo que o launch põe em cada linha
# ([nome_do_processo-N]). O detalhe de cada nó fica em ros_log/.
if [ -f "$PASTA/container.log" ]; then
  grep -E '^\[patrulha-[0-9]+\]' "$PASTA/container.log" > "$PASTA/patrulha.log" || true
  grep -E '^\[base_falsa-[0-9]+\]' "$PASTA/container.log" > "$PASTA/base_falsa.log" || true
  grep -vE '^\[(patrulha|base_falsa|vigia_l1)-[0-9]+\]' "$PASTA/container.log" > "$PASTA/nav2.log" || true
fi

{
  echo "cenario: $CENARIO"
  echo "imagem: $IMAGEM ($(docker image inspect -f '{{.Id}}' "$IMAGEM" 2>/dev/null | cut -c8-19))"
  echo "teto_mb: $TETO_MB"
  echo "memoria_disponivel_antes_mb: $LIVRE_MB"
  echo "tentativas: $TENTATIVA"
  echo "oom_killed: $MORTO_POR_MEMORIA"
  echo "pico_ram: $(python3 - "$PASTA/docker_stats.csv" <<'PY'
import re, sys
fator = {'KiB': 1 / 1024, 'MiB': 1, 'GiB': 1024}
pico = 0.0
for linha in open(sys.argv[1]).read().splitlines()[1:]:
    achado = re.search(r'([\d.]+)(KiB|MiB|GiB)', linha)
    if achado:
        pico = max(pico, float(achado.group(1)) * fator[achado.group(2)])
print(f'{pico:.0f} MiB')
PY
)"
} > "$PASTA/execucao.txt"
cat "$PASTA/execucao.txt"
[ -f "$PASTA/ambiente.txt" ] && cat "$PASTA/ambiente.txt"

# SIM-06b: as tentativas acabaram e o Nav2 leve não subiu nenhuma vez.
if [ "$NAV2_NAO_SUBIU" = 1 ]; then
  echo "REPROVADO ($CENARIO): nav2_nao_subiu ($TENTATIVAS tentativas, ver nav2_tentativas.txt)" \
    | tee "$PASTA/veredito.txt"
  exit 1
fi

JSONL=$(ls "$PASTA"/*.jsonl 2>/dev/null | head -1 || true)
SINAL=""
[ -f "$PASTA/sinal.txt" ] && SINAL="--sinal $(cat "$PASTA/sinal.txt")"
set +e
# shellcheck disable=SC2086
python3 "$CONFERIR" "$CENARIO" "${JSONL:-$PASTA/sem-log.jsonl}" $SINAL | tee "$PASTA/veredito.txt"
RESULTADO=${PIPESTATUS[0]}
exit "$RESULTADO"

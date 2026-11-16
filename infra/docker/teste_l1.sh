#!/usr/bin/env bash
# Teste L1 da spec specs/patrol-inf: o nosso nó patrulha_tb4 no simulador leve
# (Nav2 + nav2_loopback_sim + base e bateria falsas), sem RViz, um cenário por vez.
#
#   ./teste_l1.sh <cenario>      roda o cenário, guarda a evidência e dá o veredito
#   ./teste_l1.sh lista          mostra os cenários
#   ./teste_l1.sh parar          desliga o container, se tiver ficado algum
#
# Cada execução deixa uma pasta em progresso/evidencias/l1/<data>-<cenario>/ com o log
# JSONL da patrulha, os logs do Nav2 e da base falsa, o pico de RAM e o veredito.
#
# Segurança do notebook (TST-06): o teste NÃO sobe se a memória disponível for menor que
# o teto do container (TETO_MB, padrão 2048) mais 1 GiB de folga. Se estourar o teto,
# só o container morre.
set -euo pipefail
cd "$(dirname "$0")/.."
RAIZ="$(cd .. && pwd)"
NOME=tb4l1
TETO_MB="${TETO_MB:-2048}"
FOLGA_MB=1024

# Padrões de cada cenário. BASE = parâmetros da base falsa; CONFIG = arquivo em config/.
CONFIG=leve_reduzido.yaml
BASE="-p battery_start:=0.90 -p drain_per_s:=0.002 -p charge_per_s:=0.05"
LIMITE_S=900          # tempo de relógio máximo do cenário
SUBIR_NAV2=1
SUBIR_BASE=1
NAV2_EXTRA=""
PATRULHA_EXTRA=""
SINAL_NO_FIM=1        # manda SIGINT quando o cenário chega ao ponto esperado (prova o PAT-15)

CENARIO="${1:-}"
case "$CENARIO" in
  ciclo)            ;;  # TST-03: um ciclo de recarga completo
  l1b)              NAV2_EXTRA="params_file:=/tmp/nav2_l1b.yaml" ;;  # H4: montado no container (ver l1_dentro.sh)
  dock_falha)       BASE="-p battery_start:=0.90 -p drain_per_s:=0.004 -p charge_per_s:=0.05 -p falhar_dock_n:=1" ;;  # TST-04
  queda_bateria)    BASE="-p battery_start:=0.99 -p drain_per_s:=0.001 -p charge_per_s:=0.05 -p queda_bateria_em_s:=12.0 -p queda_bateria_para:=0.30" ;;  # TST-05
  sem_bateria)      BASE="$BASE -p simular_bateria:=false"; LIMITE_S=120 ;;               # PAT-04
  fora_da_doca)     BASE="-p battery_start:=0.99 -p comecar_na_doca:=false"; LIMITE_S=120 ;;  # PAT-17
  sem_servidor)     BASE="$BASE -p simular_doca:=false"; LIMITE_S=120 ;;                  # PAT-20
  sem_relogio)      SUBIR_NAV2=0; SUBIR_BASE=0; PATRULHA_EXTRA="use_sim_time:=true"; LIMITE_S=60 ;;  # PAT-22
  bateria_perdida)  BASE="-p battery_start:=0.99 -p drain_per_s:=0.0005 -p charge_per_s:=0.05 -p parar_bateria_em_s:=12.0"; LIMITE_S=400 ;;  # PAT-18 e 18b
  falhas_seguidas)  CONFIG=teste_tempo_curto.yaml; BASE="-p battery_start:=0.99 -p drain_per_s:=0.0005"; LIMITE_S=400 ;;  # PAT-07, 08 e 19
  sigint)           BASE="-p battery_start:=0.99 -p drain_per_s:=0.0005" ;;               # PAT-15
  parar)
    docker rm -f "$NOME" >/dev/null 2>&1 || true
    echo "Parado."; exit 0 ;;
  *)
    sed -n 2,14p "$0"
    echo "Cenários: ciclo l1b dock_falha queda_bateria sem_bateria fora_da_doca sem_servidor"
    echo "          sem_relogio bateria_perdida falhas_seguidas sigint"
    exit 0 ;;
esac

# TST-06: recusa subir sem folga de memória.
LIVRE_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$LIVRE_MB" -lt $((TETO_MB + FOLGA_MB)) ]; then
  echo "RECUSADO (TST-06): há $LIVRE_MB MiB disponíveis; preciso de $((TETO_MB + FOLGA_MB)) MiB"
  echo "(teto de $TETO_MB MiB + folga de $FOLGA_MB MiB). Feche o navegador e os programas pesados."
  exit 3
fi

PASTA="$RAIZ/progresso/evidencias/l1/$(date +%Y-%m-%d_%H-%M-%S)-$CENARIO"
mkdir -p "$PASTA"
echo "Cenário: $CENARIO | memória disponível: $LIVRE_MB MiB | teto: $TETO_MB MiB"
echo "Evidências: $PASTA"

docker rm -f "$NOME" >/dev/null 2>&1 || true
docker run -d --name "$NOME" --init --memory="${TETO_MB}m" --memory-swap="${TETO_MB}m" --cpus=3 \
  -v "$PWD/tools:/tools:ro" -v "$PWD/docker:/infra_docker:ro" \
  -v "$RAIZ/workspace:/workspace" -v "$PASTA:/evidencias" \
  -e CENARIO="$CENARIO" -e CONFIG="$CONFIG" -e BASE="$BASE" -e LIMITE_S="$LIMITE_S" \
  -e SUBIR_NAV2="$SUBIR_NAV2" -e SUBIR_BASE="$SUBIR_BASE" -e NAV2_EXTRA="$NAV2_EXTRA" \
  -e PATRULHA_EXTRA="$PATRULHA_EXTRA" -e SINAL_NO_FIM="$SINAL_NO_FIM" \
  -e DONO="$(id -u):$(id -g)" \
  physical-ai:jazzy bash /infra_docker/l1_dentro.sh >/dev/null

# Se o usuário apertar Ctrl+C, o container não fica para trás.
trap 'docker rm -f "$NOME" >/dev/null 2>&1 || true' EXIT

# Amostra a RAM do container a cada 5 s, até ele terminar.
echo "hora,memoria" > "$PASTA/docker_stats.csv"
while [ "$(docker inspect -f '{{.State.Running}}' "$NOME" 2>/dev/null)" = "true" ]; do
  USO=$(docker stats --no-stream --format '{{.MemUsage}}' "$NOME" 2>/dev/null | cut -d/ -f1 | tr -d ' ')
  [ -n "$USO" ] && echo "$(date +%H:%M:%S),$USO" >> "$PASTA/docker_stats.csv"
  sleep 5
done

MORTO_POR_MEMORIA=$(docker inspect -f '{{.State.OOMKilled}}' "$NOME" 2>/dev/null || echo "?")
docker logs "$NOME" > "$PASTA/container.log" 2>&1 || true
docker rm -f "$NOME" >/dev/null 2>&1 || true
trap - EXIT

{
  echo "cenario: $CENARIO"
  echo "config: $CONFIG"
  echo "base_falsa: $BASE"
  echo "teto_mb: $TETO_MB"
  echo "memoria_disponivel_antes_mb: $LIVRE_MB"
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

JSONL=$(ls "$PASTA"/*.jsonl 2>/dev/null | head -1 || true)
SINAL=""
[ -f "$PASTA/sinal.txt" ] && SINAL="--sinal $(cat "$PASTA/sinal.txt")"
set +e
python3 "$PWD/tools/conferir_l1.py" "$CENARIO" "${JSONL:-$PASTA/sem-log.jsonl}" $SINAL | tee "$PASTA/veredito.txt"
RESULTADO=${PIPESTATUS[0]}
exit "$RESULTADO"

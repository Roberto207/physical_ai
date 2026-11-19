#!/usr/bin/env bash
# Constrói as imagens do projeto a partir do Dockerfile desta pasta (um alvo por imagem).
#
#   ./construir_imagem.sh [alvo...]   alvos: base robo sim llm, ou "todas"
#                                     sem alvo: robo (o que o SLAM e a patrulha no lab usam)
#
# Por que conferir a RAM: o "docker build" não tem teto de memória, e um build travou o
# notebook do Roberto (7,4 GiB) em 2026-11-05. Abaixo de 12 GiB de RAM total, o build é recusado
# (IMG-06). Na prática, as imagens são construídas no PC do laboratório.
#
# Antes do build de cada alvo, se a imagem com o mesmo nome for Jazzy, ela ganha a tag
# physical-ai:jazzy-<alvo> (PRE-02). Para voltar ao Jazzy: docs/decisoes/ADR-001-ros2-humble.md.
# Os alvos dividem camadas: construir o sim depois do robo reaproveita o que já foi baixado.
set -euo pipefail
cd "$(dirname "$0")"

MINIMO_GIB=12
DISTRO_ANTIGA=jazzy   # a distro que o PRE-02 guarda antes de sobrescrever (exceção do IMG-04)
declare -A NOME=([base]=physical-ai:base [robo]=physical-ai:robo [sim]=physical-ai:sim
                 [llm]=physical-ai:llm)

# IMG-06: a primeira coisa que o script faz. Numa máquina recusada, nem tag nem build.
# MemTotal vem em KiB. A conta inteira basta: só queremos saber se passa do mínimo.
total_gib=$(( $(awk '/^MemTotal:/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
if [ "$total_gib" -lt "$MINIMO_GIB" ]; then
  echo "RECUSADO (IMG-06): esta máquina tem ${total_gib} GiB de RAM; o mínimo para o build é ${MINIMO_GIB} GiB."
  echo "Construa no PC do laboratório."
  exit 1
fi

alvos=("$@"); [ ${#alvos[@]} -eq 0 ] && alvos=(robo)
[ "${alvos[0]}" = todas ] && alvos=(base robo sim llm)
for alvo in "${alvos[@]}"; do
  [ -n "${NOME[$alvo]:-}" ] || { echo "Alvo desconhecido: $alvo (use base, robo, sim, llm ou todas)"; exit 1; }
done

docker info >/dev/null 2>&1 \
  || { echo "O Docker não está respondendo. Ligue com: sudo systemctl start docker"; exit 1; }

# Distro gravada na imagem (variável ROS_DISTRO das imagens ros:*). Vazio se a imagem não existe.
distro_de() {
  docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" 2>/dev/null \
    | sed -n 's/^ROS_DISTRO=//p'
}

# Espaço livre onde o Docker guarda as imagens. Se não der para medir, só não avisa.
raiz_docker=$(docker info -f '{{.DockerRootDir}}' 2>/dev/null || echo /)
livre_disco_gib=$(df -BG --output=avail "$raiz_docker" 2>/dev/null | tail -1 | tr -dc '0-9' || true)
if [ -n "$livre_disco_gib" ] && [ "$livre_disco_gib" -lt 10 ]; then
  echo "AVISO: só ${livre_disco_gib} GiB livres no disco do Docker."
fi

for alvo in "${alvos[@]}"; do
  imagem=${NOME[$alvo]}
  # PRE-02: guarda a imagem antiga antes de o build reaproveitar o nome dela.
  if [ "$(distro_de "$imagem")" = "$DISTRO_ANTIGA" ]; then
    docker tag "$imagem" "physical-ai:$DISTRO_ANTIGA-$alvo"
    echo "Guardada: $imagem ($DISTRO_ANTIGA) -> physical-ai:$DISTRO_ANTIGA-$alvo"
  fi
  echo "== ${alvo} -> ${imagem} (RAM total: ${total_gib} GiB)"
  docker build --target "$alvo" -t "$imagem" -f Dockerfile .
  echo "   ROS_DISTRO da imagem nova: $(distro_de "$imagem")"
done
echo "Pronto. Tamanho de cada imagem: docker images 'physical-ai'"

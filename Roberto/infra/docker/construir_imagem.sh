#!/usr/bin/env bash
# Constrói as imagens do projeto a partir do Dockerfile desta pasta (um alvo por imagem).
#
#   ./construir_imagem.sh [alvo...]   alvos: base robo sim llm completa, ou "todas"
#                                     sem alvo: robo (o que o SLAM e a patrulha no lab usam)
#   ./construir_imagem.sh apelidos    NOTEBOOK: dá à physical-ai:jazzy os nomes base, robo e
#                                     sim, sem build (ela já tem tudo que essas três têm)
#
# Por que conferir a RAM: o "docker build" não tem teto de memória, e um build travou o
# notebook do Roberto (7,4 GiB) em 2026-11-05. Abaixo de 12 GiB de RAM total, o build é recusado.
# Os alvos dividem camadas: construir o sim depois do robo reaproveita o que já foi baixado.
# Tempo e disco não medidos. O peso maior esperado é o Gazebo, que só o sim e o completa têm.
set -euo pipefail
cd "$(dirname "$0")"

MINIMO_GIB=12
# Alvo do Dockerfile -> nome da imagem. O completa mantém o nome antigo (physical-ai:jazzy),
# para os scripts do simulador leve (ros.sh, treino_leve.sh, teste_l1.sh) não mudarem.
declare -A NOME=([base]=physical-ai:base [robo]=physical-ai:robo [sim]=physical-ai:sim
                 [llm]=physical-ai:llm [completa]=physical-ai:jazzy)

docker_ligado() {
  docker info >/dev/null 2>&1 || { echo "O Docker não está respondendo. Ligue com: sudo systemctl start docker"; exit 1; }
}

if [ "${1:-}" = apelidos ]; then
  docker_ligado
  docker image inspect physical-ai:jazzy >/dev/null 2>&1 \
    || { echo "Não achei a physical-ai:jazzy nesta máquina."; exit 1; }
  for alvo in base robo sim; do docker tag physical-ai:jazzy "${NOME[$alvo]}"; echo "  ${NOME[$alvo]} -> physical-ai:jazzy"; done
  echo "Apelidos criados. Nenhum build rodou. (A llm não ganha apelido: a jazzy não é ela.)"
  exit 0
fi

alvos=("$@"); [ ${#alvos[@]} -eq 0 ] && alvos=(robo)
[ "${alvos[0]}" = todas ] && alvos=(base robo sim llm completa)
for alvo in "${alvos[@]}"; do
  [ -n "${NOME[$alvo]:-}" ] || { echo "Alvo desconhecido: $alvo (use base, robo, sim, llm, completa ou todas)"; exit 1; }
done

# MemTotal vem em KiB. A conta inteira basta: só queremos saber se passa do mínimo.
total_gib=$(( $(awk '/^MemTotal:/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
if [ "$total_gib" -lt "$MINIMO_GIB" ]; then
  echo "RECUSADO: esta máquina tem ${total_gib} GiB de RAM; o mínimo para o build é ${MINIMO_GIB} GiB."
  echo "No notebook do Roberto, use: ./construir_imagem.sh apelidos"
  exit 1
fi
docker_ligado

# Espaço livre onde o Docker guarda as imagens. Se não der para medir, só não avisa.
raiz_docker=$(docker info -f '{{.DockerRootDir}}' 2>/dev/null || echo /)
livre_disco_gib=$(df -BG --output=avail "$raiz_docker" 2>/dev/null | tail -1 | tr -dc '0-9' || true)
if [ -n "$livre_disco_gib" ] && [ "$livre_disco_gib" -lt 10 ]; then
  echo "AVISO: só ${livre_disco_gib} GiB livres no disco do Docker."
fi

for alvo in "${alvos[@]}"; do
  echo "== ${alvo} -> ${NOME[$alvo]} (RAM total: ${total_gib} GiB)"
  docker build --target "$alvo" -t "${NOME[$alvo]}" -f Dockerfile .
done
echo "Pronto. Tamanho de cada imagem: docker images 'physical-ai'"

#!/usr/bin/env bash
# Executar a adaptação do tutorial Humble no TurtleBot 4 real, pelo PC.
set -euo pipefail
cd "$(dirname "$0")/../.."
# Qual robô: ROBO=robot3 workspace/patrulha_oficial/rodar.sh 1
. infra/lab/robo_ativo.sh

VOLTAS=${1:-1}
[[ "$VOLTAS" =~ ^[0-9]+$ ]] || { echo 'Uso: workspace/patrulha_oficial/rodar.sh [voltas]; 0 = contínuo'; exit 2; }

infra/docker/lab.sh conferir workspace/mapas/mapa_lab_novo.yaml
infra/docker/lab.sh robo checar-rede

for servico in localizacao nav2 rviz; do
    [ -n "$(infra/docker/lab.sh robo compose ps -q "$servico")" ] || {
        echo "Falta o contêiner $servico. Veja workspace/patrulha_oficial/README.md."
        exit 2
    }
done

# Um controlador por vez: o nó de linguagem natural também comanda o robô.
[ -z "$(docker ps -q --filter label=com.docker.compose.project=tb4-robo \
        --filter label=com.docker.compose.service=llm)" ] || {
    echo 'O nó llm está rodando e também comanda o robô. Encerre-o antes.'
    exit 2
}

echo "ROBÔ: $ROBO (namespace ${ROBO_NS:-nenhum})"
echo 'ATENÇÃO: o TurtleBot REAL fará undock e navegará sozinho.'
echo 'AGORA, antes de SIM: use 2D Pose Estimate no RViz na pose real da doca.'
echo 'Confira laser alinhado, área livre e pessoa ao lado.'
echo "Voltas solicitadas: $VOLTAS (0 = contínuo)."
read -r -p 'Digite SIM para iniciar: ' CONFIRMACAO
[ "$CONFIRMACAO" = SIM ] || { echo 'Cancelado.'; exit 1; }

infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop.py --voltas "$VOLTAS" \
    --ros-args ${ROBO_NS:+-r "__ns:=$ROBO_NS"}

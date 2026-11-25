#!/usr/bin/env bash
# Executar a adaptação do tutorial Humble no TurtleBot 4 real, pelo PC.
set -euo pipefail
cd "$(dirname "$0")/../.."

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

echo 'ATENÇÃO: o TurtleBot REAL fará undock e navegará sozinho.'
echo 'AGORA, antes de SIM: use 2D Pose Estimate no RViz na pose real da doca.'
echo 'Confira laser alinhado, área livre e pessoa ao lado.'
echo "Voltas solicitadas: $VOLTAS (0 = contínuo)."
read -r -p 'Digite SIM para iniciar: ' CONFIRMACAO
[ "$CONFIRMACAO" = SIM ] || { echo 'Cancelado.'; exit 1; }

infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/upstream/patrol_loop.py --voltas "$VOLTAS" \
    --ros-args -r __ns:=/robot1

#!/usr/bin/env bash
# Para tudo do projeto neste PC. O LLM e a patrulha recebem SIGTERM e cancelam a meta antes.
docker stop -t 15 tb_llm tb_patrulha >/dev/null 2>&1 || true
ids=$(docker ps -aq --filter label=tb4.robo)
[ -z "$ids" ] || docker rm -f $ids >/dev/null
xhost -SI:localuser:root >/dev/null 2>&1 || true   # desfaz a permissão de tela do RViz
echo "Parado."

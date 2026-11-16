cd ~/dev/physical_ai/infra/docker

./treino_leve.sh iniciar --patrulha   # sobe Nav2 + simulador leve + base/bateria falsas + patrol_loop
# espere cerca de 20 s
./treino_leve.sh logs                 # mostra o que a patrulha está dizendo

O script sobe o Nav2 com o nav2_loopback_sim, que simula o robô sem Gazebo, no mapa warehouse. Depois de 15 s ele sobe fake_tb4_base.py, que simula a base e a bateria. Aos 20 s ele inicia o patrol_loop.

Opções

┌────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────┐
│      Comando       │                                        O que faz                                         │
├────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
│ iniciar            │ Sobe só o Nav2 e a base falsa, sem patrulha. Use quando quiser rodar o seu código à mão. │
├────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
│ iniciar --patrulha │ Também roda o patrol_loop oficial.                                                       │
├────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
│ iniciar --rviz     │ Abre o RViz. Ele usa X11 e xhost, e a RAM sobe de cerca de 500 MiB para 870 MiB.         │
├────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
│ terminal           │ Abre um shell ROS dentro do container. A pasta workspace/ aparece em /workspace.         │
├────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
│ parar              │ Remove o container e libera a memória.                                                   │
└────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────┘

Para testar a lógica de bateria, mude os valores iniciais assim:

BATERIA_INICIAL=0.3 DESCARGA=0.001 ./treino_leve.sh iniciar --patrulha


A nossa patrulha (pacote patrulha_tb4, spec specs/patrol-inf)

Testes da lógica, sem ROS e sem Docker (segundos):

cd ~/dev/physical_ai/workspace/meu_ws/src/patrulha_tb4
python3 -m pytest -q                  # 124 testes
python3 test/checar_rastreio.py       # todo requisito L0 tem teste?

Conferir uma configuração contra o mapa, antes de o robô andar:

python3 -m patrulha_tb4.pontos config/inf_lab.yaml

Teste no simulador leve, um cenário por vez. Feche o navegador antes: o script recusa subir com menos de 3 GiB disponíveis.

cd ~/dev/physical_ai/infra/docker
./teste_l1.sh lista                   # mostra os cenários
./teste_l1.sh ciclo                   # ciclo de recarga completo (cerca de 7 min)
./teste_l1.sh dock_falha              # o dock falha 1 vez e a patrulha tenta de novo

Cada execução deixa uma pasta em progresso/evidencias/l1/ com o log JSONL, os logs do Nav2 e o veredito (APROVADO ou REPROVADO). O que foi feito e por quê está em docs/registro-de-mudancas.md.

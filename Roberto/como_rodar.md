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


Modo laboratório: Docker Compose (desde 2026-11-16)

Só no PC do laboratório. No notebook, o Gazebo e o docker build não cabem na memória.
Os serviços ficam em infra/compose/sim.yaml (Gazebo) e infra/compose/robo.yaml (robô real).
O atalho infra/docker/lab.sh chama o arquivo certo e confere a rede antes.

cd ~/physical_ai/Roberto/infra/docker   # no PC do lab (NUC14RVK-B); no notebook, ~/dev/physical_ai
./construir_imagem.sh base robo sim   # 1ª vez no PC (recusa com menos de 12 GiB de RAM). O robo.yaml usa a base
./construir_imagem.sh apelidos        # SÓ NO NOTEBOOK: dá à physical-ai:jazzy os nomes base, robo e sim

Treino do mapa no Gazebo (rede isolada e domínio 42, não alcança o robô real):

./lab.sh sim subir gazebo slam rviz   # espere cerca de 1 min (./lab.sh sim logs gazebo)
./lab.sh sim undock                   # tira o robô simulado da doca
./lab.sh sim teleop                   # dirige pelo teclado, a 0,15 m/s
./lab.sh sim salvar teste_maze        # grava em workspace/mapas/ e confere
./lab.sh sim parar

ATENÇÃO (2026-11-16): não use o lab.sh robo por enquanto. A imagem do PC é Jazzy e derruba o robô, que é Humble.
Falta fazer a imagem Humble (docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md, seção 8).

Mapa no robô real, só depois das etapas 1 a 3 do kit de campo (specs/patrol-inf/kit-de-campo.md):

./lab.sh robo checar-rede             # só lê: rotas, e /robot1/scan, /robot1/tf e /robot1/odom chegam?
./lab.sh robo subir slam rviz         # confere a rede e sobe (não move o robô)
./lab.sh robo teleop                  # move o robô REAL: pede que você digite SIM
./lab.sh robo salvar lab
./lab.sh robo parar

Patrulha no robô real (kit de campo, etapas 5 a 8):

MAPA=/mapas/lab.yaml ./lab.sh robo subir localizacao nav2 rviz
CONFIG=/mapas/inf_lab_preenchido.yaml ./lab.sh robo patrulha   # config ao lado do mapa; validar_pontos + SIM antes de andar

Ver o que está rodando: ./lab.sh robo estado. Conferir um mapa: ./lab.sh conferir workspace/mapas/lab.yaml (caminho a partir da pasta Roberto/: o lab.sh vai para lá antes)
O robô do lab é Humble, usa Discovery Server e o namespace /robot1 (ROBO_NS muda; ROBO_NS= para nenhum).
O PC precisa de rotas pelo robô para 192.168.186.0/24 e 192.168.185.0/24: o checar-rede mostra o comando.
Acesso ao robô por cabo e por Wi-Fi (`ssh robo`, `ssh robo-wifi`) e as rotas: docs/acesso-ao-robo-por-cabo.md.
O que foi conferido no robô: docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md. A rede do PC fica em infra/lab/rede_lab.env. Explicação: docs/tarefas/2026-11-16-compose-e-alvos.md

# Patrulha pelo exemplo oficial no mapa_lab_novo

Fonte: [turtlebot4_tutorials, `patrol_loop.py`, ramo Humble](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py) e [manual oficial TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html). O exemplo oficial é para simulação e precisa de destinos, mapa e orientação adaptados para o robô físico. O método `getPoseStamped` aceita yaw em graus.

Preparado `workspace/patrulha_oficial/`: cópia intacta em `upstream/patrol_loop.py`, adaptação em `patrol_loop.py`, guia em `README.md` e comando protegido em `rodar.sh`. Pontos usados de `docs/rascunho/possiveis_points.md`: início `(-0.203, 0.100, 38.48°)`; destinos `(-0.586,-0.807)`, `(-3.550,-3.063)`, `(-5.608,-0.823)`, `(-1.967,1.030)` com os yaw anotados. Na primeira prova, `rodar.sh 1` faz uma volta e tenta a doca; `0` repete até bateria baixa ou interrupção. Em falha de destino, para sem enviar o próximo.

Em 23/11: `mapa_lab_novo.yaml/.pgm` validados como utilizáveis. Cinco pings PC→robô sem perda (1,7–86 ms). `lab.sh robo checar-rede` OK para scan, tf, odom, bateria e dock. Localização subida com o mapa, seguida de Nav2 e RViz. `/robot1/dock_status` respondeu `is_docked: true`. AMCL exigiu pose inicial; primeira publicação única terminou antes da descoberta ROS e não chegou. O script foi ajustado para repetir a publicação até receber `/robot1/amcl_pose`. Nova execução `--somente-pose` confirmou no AMCL `Setting pose: -0.203 0.100 0.672` e no Nav2 `Managed nodes are active`. Ainda não houve ensaio de movimento com esse script. `py_compile`, `bash -n` e importação/`--help` no contêiner Humble passaram.

Correção solicitada pelo usuário: os graus anotados em `possiveis_points.md` não foram confirmados e não devem ser usados. A adaptação passou a armazenar somente `x,y` dos quatro pontos, calcular a orientação de cada meta pela direção do ponto seguinte e calcular a orientação da aproximação pela direção da doca. O programa não publica mais pose inicial. O operador deve usar **2D Pose Estimate** no RViz após abrir a localização e confirmar alinhamento do laser; o programa só verifica que `map→odom` está recente. A publicação automática anterior foi uma etapa somente de preparação e não enviou movimento. Antes de `rodar.sh 1`, confirmar visualmente robô e laser na posição real da doca e pessoa acompanhando. O ensaio físico ainda não foi feito.

Depois de `rodar.sh 1` falhar na checagem de rede, o ping ao Raspberry Pi estava bom e `turtlebot4.service` e processo Fast DDS Discovery Server estavam ativos. Entretanto, `ros2 topic list` no próprio Pi mostrou apenas `/parameter_events` e `/rosout`. Seguindo o manual oficial do Discovery Server, o usuário executou `ros2 daemon stop; ros2 daemon start; ros2 topic list`; a lista completa reapareceu, incluindo `/robot1/scan`, `/robot1/odom`, `/robot1/tf`, bateria e doca. `infra/docker/lab.sh robo checar-rede` no PC então voltou a `REDE OK`. Os contêineres de localização, Nav2 e RViz haviam sido reiniciados no PC durante o diagnóstico, portanto a pose inicial precisa ser marcada de novo com 2D Pose Estimate antes de qualquer movimento. Nenhum movimento foi enviado pelo script adaptado.

Nova tentativa `rodar.sh 1`: passou mapa e rede, recebeu `SIM`, registrou `map→odom` recente e ficou parada sem undock. O AMCL havia recebido o 2D Pose Estimate e o Nav2 tinha `Managed nodes are active`. A causa foi identificada no código: `waitUntilNav2Active()` do navegador oficial espera uma mensagem `initialpose` recebida *pelo próprio nó*, mas o operador a havia enviado antes de esse nó existir. O script foi corrigido para `waitUntilNav2Active(localizer='map_server')`, que ainda espera os serviços ativos mas não repete a espera por initialpose; sua verificação prévia de TF já exige localização. A tentativa anterior foi interrompida sem movimento. Um teste sem movimento da correção, feito minutos depois, recusou iniciar porque `map→odom` já tinha ficado antigo com o robô parado. O `rodar.sh` passou a instruir o operador a usar 2D Pose Estimate **no prompt antes de digitar SIM**, após a checagem de rede, para que a TF esteja recente quando o novo nó iniciar. Aguardando nova pose manual e validação curta, sem movimento.

Outra tentativa com 2D Pose Estimate no prompt ainda registrou `map→odom` recente e parou antes do undock. O Nav2 tinha nós ativos, mas `waitUntilNav2Active(localizer='map_server')` continuava dependendo de respostas dos serviços de ciclo de vida via DDS, que podem demorar indefinidamente neste laboratório. A tentativa foi interrompida pelo operador sem movimento. A espera foi substituída por checagem com prazo de 30 s das ações `navigate_to_pose`, `dock` e `undock`, após exigir TF recente. Um teste **somente de leitura**, importando a função adaptada no contêiner Humble, mostrou as três ações disponíveis em aproximadamente 2 s. `py_compile` passou e não havia processo anterior de patrulha ativo. Próxima execução requer de novo 2D Pose Estimate no prompt, confirmação visual do laser e supervisão física.

Revisão prévia adicional: as imagens `physical-ai:base` e `physical-ai:robo` têm ROS Humble; `localizacao`, `nav2` e `rviz` estavam em execução. `lab.sh robo checar-rede` retornou REDE OK. O log do Nav2 terminou com `Managed nodes are active`. Os quatro destinos e a doca estão em células livres; a menor distância de um destino a célula não livre/ocupada é 0,50 m (o raio configurado do robô é 0,175 m). Isto verifica somente o mapa salvo, não a rota atual no costmap ou obstáculos presentes. Um destino sem conclusão passou a ser cancelado após 120 s. `bash -n` e `py_compile` passaram. Não houve ensaio físico da rota; a aproximação e o encaixe na doca permanecem sem confirmação. As chamadas oficiais de dock/undock ainda podem esperar sem prazo em falha de comunicação.

Ensaio físico informado pelo operador: `rodar.sh 1` fez undock, alcançou com sucesso os quatro pontos e concluiu uma volta. Na volta à doca, a meta de navegação para `(-0.586, -0.807)` falhou com `TaskResult.FAILED` após cerca de 47 s; o script interrompeu a patrulha e não enviou `dock()`. O ponto é livre no mapa, mas o caminho de retorno e sua orientação de aproximação ainda exigem inspeção no RViz/costmap. Não repetir a volta completa como diagnóstico. Próxima recuperação: conferir se o robô vê a doca em `/robot1/dock_status` (`dock_visible`); se não, aproximar e alinhar manualmente sob supervisão, então usar a ação `dock` do TurtleBot 4 Standard. O manual oficial do Create 3 diz que `Dock` falha quando a doca está distante ou não visível.

Na recuperação, `ros2 topic echo --once /robot1/dock_status` sem tipo explícito falhou na descoberta do tópico. Com tipo e QoS explícitos (`irobot_create_msgs/msg/DockStatus --qos-profile sensor_data`), respondeu `dock_visible: false` e `is_docked: false`. Portanto, não enviar dock ainda: aproximar manualmente usando o controle, verificar novamente `dock_visible`, depois acionar Dock no HMI.

Diagnóstico do retorno antes da próxima volta: `dock_status` posterior confirmou `is_docked: true`. O Nav2 começou a navegar de aproximadamente `(-2.09, 1.01)` até `(-0.59, -0.81)` e, 7 s depois, o DWB reportou `No valid trajectories out of 419` e `BaseObstacle/Trajectory Hits Obstacle`. Spin e backup de recuperação também registraram `Collision Ahead`. A linha direta entre os pontos atravessa somente células livres no PGM. Assim, o erro registrado é bloqueio no costmap local logo após o ponto 4, não prova coordenada errada da doca; conferir no RViz o laser, local costmap e obstáculos físicos no trecho antes de repetir. O programa já tenta dock após aproximação bem-sucedida, mas não o faz se a navegação falhar.

Integração com o trabalho paralelo: após `git fetch`, a `main` local avançou sem conflito de `54cd236` para `29cf7e6`, commit de documentação do colega. A branch remota `v2-patrol-oficial` (`2e32853`) contém outro experimento em `v2/`, com Docker/parametrização própria e yaw manual, ainda não rodado no robô segundo seu README. Esta adaptação em `workspace/patrulha_oficial/` é a que completou os quatro pontos no TurtleBot físico; a v2 continua separada para evitar executar dois stacks de localização/Nav2 ao mesmo tempo. O commit remoto de `main` não alterou os arquivos da patrulha usada nesta sessão.

Atualização solicitada em 23/11/2026: Publish Point forneceu novo ponto 1 `(-0.4172118008136749, -0.32544219493865967)` e novo ponto 4 `(-0.9465320706367493, 2.065439224243164)`. Substituem os valores anteriores: ponto 1 `(-0.5858250856399536, -0.8073815107345581)` e ponto 4 `(-1.9671252965927124, 1.0304899215698242)`. Pontos 2 e 3 e doca permanecem inalterados. O ponto 1 continua sendo usado como aproximação da doca; conferir no RViz/costmap se esse novo local e o trajeto de retorno estão livres antes de executar. Ainda não validado fisicamente com as coordenadas novas.

## Problemas do Nav2 no ensaio com os pontos novos (23/11/2026, noite)

Três tentativas de `rodar.sh 1` com os pontos 1 e 4 novos. Nenhuma completou o ponto 1. A causa raiz da primeira falha não foi determinada; a das outras duas tem uma hipótese ainda não confirmada.

**1. Falha no ponto 1 (`TaskResult.FAILED` após cerca de 78 s).** O robô saiu da doca e ficou parado. No log do Nav2: `backup` com `Exceeded time allowance`, `bt_navigator` estourando os 10 Hz, timeouts de serviço e de ação dentro do próprio Nav2 (`clear_entirely_local_costmap`, `spin`, `wait`) e scans descartados (`earlier than all the data in the transform cache`). Medição sem movimento: atraso mediano do scan 0,22 s (máximo 0,41 s), odom 0,14 s e tf 0,11 s, sem perda em massa. Essa latência sozinha não explica 78 s parado. O RViz usava entre 177% e 300% de CPU, hipótese não confirmada. O `cmd_vel` não pôde ser inspecionado porque a CLI não enxerga tópicos pelo Discovery Server.

**2. Nav2 subido sem a pose inicial.** O Nav2 sobe sem o frame `map` e aborta (`Failed to bring up all requested nodes. Aborting bringup`) se for iniciado antes do 2D Pose Estimate. Ordem que funcionou: localização, RViz, 2D Pose Estimate, só então o Nav2. O README ainda lista o Nav2 junto do RViz, antes da pose.

**3. Contêiner reiniciado com `docker restart`.** Depois dele, o costmap global ficou sem mapa (`Can't update staticcostmap layer, no map received`; tamanho padrão 4,95 m × 4,95 m; `Robot is out of bounds of the costmap`). O `map_server` estava ativo e o mapa chegava a um assinante na própria localização, mas não ao Nav2 reiniciado. Recriar o contêiner pelo `lab.sh` (`robo compose rm -sf nav2` seguido de `robo subir nav2`) fez os dois costmaps receberem `271 X 179`. Não reiniciar o Nav2 com `docker restart`. O comando `lab.sh robo parar <serviço>` **derruba todos os serviços**, não só o indicado.

**4. Queda por heartbeat logo após o `docker pause` do RViz.** O contêiner do RViz foi pausado para aliviar a CPU. Em seguida:
- o `lifecycle_manager` da localização registrou `CRITICAL FAILURE: SERVER amcl IS DOWN after not receiving a heartbeat for 4000 ms` e desligou a localização, perdendo a pose e o `map→odom`;
- com o RViz ainda pausado, um novo Nav2 imprimiu `Managed nodes are active` e, menos de 0,2 s depois, `CRITICAL FAILURE: SERVER waypoint_follower IS DOWN after not receiving a heartbeat`, desativando todos os nós. `planner_server` e `behavior_server` ficaram `inactive`.

Com o Nav2 inativo, o `bt_navigator` recusou a meta do ponto 1 (`Goal ... was rejected!`) logo após o undock, e o robô ficou fora da doca. Em uma tentativa anterior com o robô fora da doca, o script se recusou corretamente a começar (`Robô não confirmado na doca`).

**Hipótese ainda não confirmada:** os contêineres usam `ipc: host` (memória compartilhada do Fast DDS). Um participante congelado por `docker pause` pode bloquear a memória compartilhada e perder os heartbeats do `bond` dos outros. Os dois horários batem com a pausa, e o Nav2 que ativou direito (20:28) era anterior a ela. Falta testar sem pausar o RViz.

**Lição sobre verificação:** `Managed nodes are active` aparece mesmo quando os nós caem logo depois. Antes de liberar o `rodar.sh`, conferir que os nós continuam ativos pelo menos 60 s depois, consultando `/robot1/<nó>/get_state`.

**Estado ao registrar:** robô fora da doca; o `rodar.sh` exige o robô na doca. Pendente: derrubar tudo, subir sem pausar o RViz, marcar a pose, subir o Nav2 e validar a estabilidade. Alternativa: tornar a checagem do contêiner `rviz` opcional no `rodar.sh`, para poder parar o RViz de verdade.

## Possível erro a verificar depois: nova falha no ponto 1 (23/11/2026, noite)

Subida na ordem do README (localização, Nav2 e RViz, sem `docker pause`), 2D Pose Estimate antes do `SIM`. `rodar.sh 1`: undock concluído, meta ao ponto 1 enviada e `TaskResult.FAILED` após cerca de 53 s. O robô saiu da doca e a patrulha parou.

Log do Nav2 no momento da falha:
- `Node timed out while executing service call to global_costmap/clear_entirely_global_costmap` e o mesmo para o `local_costmap`;
- `Timed out while waiting for action server to acknowledge goal request` para `spin` e `wait`;
- `Collision Ahead - Exiting Spin`;
- `backup` com `Exceeded time allowance before reaching the DriveOnHeading goal`;
- `Goal failed`.

É o mesmo padrão da primeira falha da noite (timeouts de serviço e ação dentro do Nav2, recuperações sem sucesso). Isso sugere que a causa não é o `docker pause` do RViz, que não estava pausado desta vez, e continua sem explicação. Não verifiquei se os nós do Nav2 permaneciam ativos durante a tentativa.

Observação: nesta execução o script usou o ponto 1 **antigo** (`-0.586, -0.807`), e o arquivo `patrol_loop.py` está com os pontos 1 e 4 antigos. A reversão não foi feita por esta sessão; confirmar com quem alterou. Isso também significa que a falha ocorreu no ponto antigo, que no ensaio anterior (quatro pontos concluídos) tinha funcionado.

A verificar na próxima sessão:
1. Confirmar quais coordenadas estão valendo e por que o arquivo voltou.
2. Antes do `rodar.sh`, conferir `get_state` de todos os nós do Nav2 e do AMCL, e repetir após 60 s.
3. Durante a tentativa, acompanhar `cmd_vel` e o heartbeat dos nós (`CRITICAL FAILURE ... heartbeat`).
4. Comparar com o ensaio que completou os quatro pontos: o que estava diferente na subida (ordem dos serviços, RViz, pose, mapa recebido pelos dois costmaps).
5. Testar o efeito de ter o RViz fechado de verdade (hoje o `rodar.sh` exige o contêiner).

## Correção de 25/11: a hipótese de memória compartilhada está descartada

A explicação registrada acima para as quedas após o `docker pause` (memória compartilhada do Fast DDS) está errada: `infra/lab/rede_lab.env` define `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` desde 21/11, portanto os contêineres do modo robo trocam dados por UDP. Resta só a coincidência de horários; a causa das quedas por heartbeat continua desconhecida.

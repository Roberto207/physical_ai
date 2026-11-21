# Patrulha no mapa_lab_novo (TurtleBot 4 Standard)

Data: 2026-11-21. Guia operacional baseado em `como_rodar_patrol_loop.md`, `kit-de-campo.md`, `infra/docker/lab.sh`, `infra/compose/robo.yaml` e no [manual oficial de navegação](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html). O usuário preencheu três pontos em `workspace/mapas/patrulha_mapa_lab_novo.yaml`; o validador ROS retornou APROVADA. As primeiras tentativas fizeram undock, mas o Nav2 abortou os destinos; o perfil foi ajustado em seguida e ainda precisa de ensaio físico.

## Ensaio de dois pontos após o ajuste do Nav2

O arquivo `workspace/mapas/patrulha_teste_pontos_1_2.yaml` contém somente os antigos `pontos[1]` e `pontos[2]` da configuração completa, nessa ordem: `(-5.608, -0.823)` e `(-1.967, 1.030)`. No log do ensaio, eles aparecerão como `ponto=0` e `ponto=1`. A primeira falha de destino manda o robô tentar retornar à doca. O validador geométrico local respondeu APROVADA, mas não comprova que as rotas funcionam.

**Pendente antes de autorizar movimento:** após o reinício do Nav2, o planejador ainda descarta scans por timestamp anterior ao cache de transformações, inclusive com o robô parado. O parâmetro `use_sim_time` do planejador foi confirmado `False`; os timeouts de 20 ms foram corrigidos, mas o problema de TF permanece. Diagnosticar TF/laser antes de executar os comandos abaixo. O código está preparado, não houve teste físico com este arquivo.

1. Confirmar que o robô está fisicamente encaixado e que `/robot1/dock_status` informa `is_docked: true`. O último valor lido nesta sessão foi true. Confirmar no RViz a posição e orientação reais na doca; a patrulha publicará novamente sua `pose_inicial`, atualmente `(-0.203, 0.100, 38.48°)`, sobrescrevendo eventual marcação manual diferente.
2. Com área livre e pessoa ao lado, em terminal A no PC: `cd ~/physical_ai` e `CONFIG=/mapas/patrulha_teste_pontos_1_2.yaml infra/docker/lab.sh robo patrulha`. A validação será repetida; conferir as duas poses e digitar `SIM`. O programa faz undock automaticamente.
3. Observar o terminal e o RViz. O sucesso esperado é `destino_ok ponto=0` seguido de `destino_ok ponto=1`. Se algum destino falhar, interromper o ensaio e guardar o log; o arquivo de teste manda voltar à doca após a primeira falha, mas o encaixe não é garantido.
4. Logo depois do segundo sucesso, em terminal B no PC, executar `infra/docker/lab.sh robo voltar-doca` e digitar `SIM`. O pedido pode cancelar o próximo destino, pois o programa entra em loop. A resposta do serviço confirma só o recebimento do pedido; aguardar `dock_ok` e `is_docked: true` antes de considerar o ensaio encerrado. `Ctrl+C` cancela onde o robô estiver e não garante a volta à doca.
5. Se os dois pontos e o retorno funcionarem, usar a configuração completa **sem editá-la**: `CONFIG=/mapas/patrulha_mapa_lab_novo.yaml infra/docker/lab.sh robo patrulha`. Conferir que a validação mostra três pontos, digitar `SIM` e acompanhar `destino_ok ponto=0`, `ponto=1`, `ponto=2`. Após uma volta completa, usar `infra/docker/lab.sh robo voltar-doca` em outro terminal, confirmar `dock_ok` e `is_docked: true`. Se falhar, guardar o log Nav2 e o da patrulha antes de tentar novamente.

## Estado e condição de partida

`workspace/mapas/mapa_lab_novo.yaml` e `.pgm` existem; `lab.sh conferir` respondeu UTILIZÁVEL. O mapa contém cerca de 59,8% de área desconhecida; planejar destinos somente na área livre efetivamente mapeada e conferir as paredes no RViz. A ficha `.info.txt` não foi produzida pelo comando de salvar que ficou preso. O robô ficou onde terminou o SLAM: **a patrulha exige que comece encaixado na doca**. Permanecer imóvel fora dela não substitui essa exigência; o nó retorna código 6. Não iniciar a patrulha antes de recolocá-lo na doca e verificar `is_docked: true`.

## 1. Preparar no PC

1. `cd ~/physical_ai`; confirmar robô energizado, doca energizada, área livre, pessoa de segurança ao lado, controle PS4 disponível e nenhum modo sim rodando.
2. `infra/docker/lab.sh robo checar-rede` deve mostrar REDE OK, inclusive `/robot1/odom`. Se faltar, conferir `create3_republisher` no Raspberry Pi; ele já caiu depois de um undock nesta sessão.
3. `infra/docker/lab.sh conferir workspace/mapas/mapa_lab_novo.yaml` deve mostrar UTILIZÁVEL.
4. Recolocar o robô na doca com supervisão, usando o procedimento manual conhecido da equipe; confirmar `is_docked: true` pelo menu/indicadores e por `/robot1/dock_status` quando possível. Se o robô foi carregado manualmente, reiniciar a localização a partir da doca.
5. `infra/docker/lab.sh robo compose stop slam`; não usar SLAM e localização ao mesmo tempo. `MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao nav2 rviz`; `infra/docker/lab.sh robo estado` deve mostrar os três serviços.
6. No RViz, Fixed Frame `map`, tópico Map `/robot1/map`. Na doca, usar **2D Pose Estimate** com a posição e orientação reais; conferir laser e paredes alinhados. O nó de patrulha também publica a pose de `pose_inicial`, mas o alinhamento deve ser confirmado antes de autorizar movimento.

## 2. Medir coordenadas e configurar

O RViz deste Compose roda no namespace `/robot1`. Inspeção direta com `ros2 node info /robot1/rviz2` confirmou que ele publica **`/robot1/clicked_point`** (`geometry_msgs/msg/PointStamped`), além de `/robot1/initialpose`. O comando de listagem dentro de `ferramentas` não mostrou o tópico mesmo após o clique; por isso não usar esse `grep` como requisito. Em um terminal no PC, escutar diretamente **dentro do próprio contêiner RViz**: `infra/docker/lab.sh robo compose exec -T rviz bash -lc 'source /opt/ros/humble/setup.bash; ros2 topic echo /robot1/clicked_point geometry_msgs/msg/PointStamped'`. Deixar o comando rodando e clicar novamente no RViz com **Publish Point**. Registrar `point.x` e `point.y` de cada clique na doca, na aproximação a 0,5 a 1 m da doca, e em áreas livres da patrulha. `Ctrl+C` encerra o echo. A ferramenta não fornece yaw. Para calculá-lo, clicar no centro do destino A e depois em um ponto B à frente dele na direção desejada; `yaw_graus = degrees(atan2(B_y-A_y, B_x-A_x))`, por exemplo com `python3 -c 'import math; print(math.degrees(math.atan2(BY-AY, BX-AX)))'` após substituir números. **A orientação da câmera do RViz pode girar o mapa na tela; direita/cima visuais não correspondem necessariamente aos eixos x/y.** O yaw da aproximação deve apontar para a doca. A posição da doca é a do centro do robô encaixado, não a da tomada.

Copiar `workspace/meu_ws/src/patrulha_tb4/config/inf_lab.yaml` para `workspace/mapas/patrulha_mapa_lab_novo.yaml`. Editar `mapa: mapa_lab_novo.yaml`, `pose_inicial`, `aproximacao_doca` e `pontos` com as medições. Para a primeira rodada, deixar só um ponto próximo da doca. Manter `ambiente: real`, `modelo: standard`, `bateria.modo: absoluto`, `tempos.bateria_perdida_s: 30` salvo se a medição da bateria pedir valor maior. Não copiar coordenadas de outro mapa. Validar no PC: `PYTHONPATH=workspace/meu_ws/src/patrulha_tb4 python3 -m patrulha_tb4.pontos workspace/mapas/patrulha_mapa_lab_novo.yaml`. Precisa dizer APROVADA. A validação testa ocupação e margem de 0,25 m, mas não prova rota contínua ou alinhamento do robô.

## 3. Rodada de um ponto

Confirmar que o robô está encaixado, `is_docked: true`, localização alinhada e Nav2 ativo. Pessoa de segurança ao lado. Em terminal dedicado: `CONFIG=/mapas/patrulha_mapa_lab_novo.yaml infra/docker/lab.sh robo patrulha`. O comando valida de novo e pede `SIM`; só digitar depois de conferir as condições. O nó faz undock e tenta o primeiro destino. Acompanhar RViz e terminal. Após uma ou duas idas, pedir volta à doca, em outro terminal: `infra/docker/lab.sh robo voltar-doca` (pede `SIM`). Esperar o encaixe confirmado e o encerramento do nó. Em falha de segurança, parar de imediato; `Ctrl+C` cancela a patrulha, mas pode deixar o robô fora da doca.

## 4. Loop completo e encerramento

Editar `pontos` para incluir todos os destinos medidos, em ordem. Validar de novo com o mesmo comando. Com o robô novamente na doca, confirmar a pose, e executar `CONFIG=/mapas/patrulha_mapa_lab_novo.yaml infra/docker/lab.sh robo patrulha`. Cada ponto deve produzir `destino_ok` no log, e a sequência deve repetir. Para encerrar de modo que o robô volte à doca, usar `infra/docker/lab.sh robo voltar-doca` em outro terminal e esperar `is_docked: true` e o resumo no log. Conferir `workspace/logs/*.jsonl`. O ciclo de recarga é uma etapa separada: o modo absoluto pode demorar horas até a bateria atingir o limite baixo; para o ensaio acelerado, consultar a seção 9 do `kit-de-campo.md` e usar `modo: relativo` apenas após validar o loop e a volta à doca.

## Diagnóstico rápido

- Sem `/robot1/odom`: não iniciar; conferir `systemctl status turtlebot4` no Raspberry Pi e o `create3_republisher`.
- Mapa ou laser desalinhado: corrigir 2D Pose Estimate antes de mover autonomamente.
- Código 6: robô começou fora da doca; encaixar e confirmar `is_docked`.
- Código 7/8: conferir logs de `nav2` e `localizacao` (`infra/docker/lab.sh robo logs nav2`, idem `localizacao`).
- Configuração recusada: revisar pontos, mapa e margem; nunca forçar o movimento ignorando `validar_pontos`.

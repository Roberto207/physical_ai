# Patrulha pelo exemplo oficial Humble, no TurtleBot 4 Standard físico

Origem: [`turtlebot/turtlebot4_tutorials`, ramo `humble`, `patrol_loop.py`](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py). Cópia intacta em `upstream/patrol_loop.py` (Apache-2.0). `patrol_loop.py` é a adaptação para `mapa_lab_novo` e `/robot1`.

O [manual oficial](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) diz que o exemplo original é para simulação e requer destinos e mapa próprios no robô físico. Nosso script usa `TurtleBot4Navigator` e as coordenadas `x, y` de `docs/rascunho/possiveis_points.md`. Os graus anotados no rascunho não são usados: o script calcula a orientação de cada destino pela direção do ponto seguinte.

## Preparar no PC

Na raiz `~/physical_ai`:

```bash
infra/docker/lab.sh robo checar-rede
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2 rviz
infra/docker/lab.sh robo estado
```

**Depois de subir a localização**, no RViz, com o robô encaixado na doca, usar **2D Pose Estimate** na posição e direção reais do robô. Conferir se o laser coincide com as paredes. O script não publica uma pose inicial e exige uma transformação `map→odom` recente antes de mover. Confirmar no log do Nav2 `Managed nodes are active`. Se o alinhamento estiver errado, não executar movimento.

## Uma volta supervisionada

```bash
workspace/patrulha_oficial/rodar.sh 1
```

O script verifica mapa, rede, contêineres e pede `SIM`. Com bateria acima de 20% e robô na doca, faz undock, visita os quatro pontos do rascunho na ordem e tenta voltar à doca após a volta. **Ao falhar qualquer destino, para e não envia o próximo.** A posição `ponto 1` também é a aproximação da doca. Antes de rodar, uma pessoa deve permanecer ao lado do robô com área livre e possibilidade de pará-lo.

Cada destino tem limite de 120 s; ao excedê-lo, o script cancela a meta e para. O limite não cobre uma resposta inicial do servidor de ação que nunca chegue nem as rotinas oficiais de dock/undock, que podem esperar indefinidamente em caso de falha de comunicação. Se o robô não avançar, use `Ctrl+C`, confira sua posição física e os logs do Nav2 antes de tentar de novo.

`workspace/patrulha_oficial/rodar.sh 0` repete as voltas até bateria baixa ou `Ctrl+C`. Se a bateria baixar, tenta aproximar e encaixar, depois encerra. `Ctrl+C` cancela a tarefa ativa, mas **não garante retorno à doca**; conferir fisicamente e por `/robot1/dock_status`.

Logs úteis: `infra/docker/lab.sh robo logs nav2` e `infra/docker/lab.sh robo logs localizacao`. O arquivo antigo `workspace/mapas/patrulha_mapa_lab_novo.yaml` pertence ao outro programa e não é lido por este script.

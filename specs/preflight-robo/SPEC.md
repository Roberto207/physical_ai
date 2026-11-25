# SPEC: skill `preflight-robo`

**Status:** Aprovada em 2026-11-25 (portão da skill `/sdd`). Implementar no PC do laboratório.
**Rigor:** spec leve (decisão do Roberto).

## 1. Objetivo

Uma skill do Claude Code que, antes de a patrulha oficial mover o TurtleBot 4, confere PC, rede, robô e Nav2, sobe no PC o que faltar (com OK) e responde `APROVADO` ou `REPROVADO`, item por item.

## 2. Contexto

As falhas de 21 e 23/11 aconteceram em condições que podem ser conferidas antes do movimento (`docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`): Nav2 iniciado antes da pose inicial aborta; `Managed nodes are active` apareceu e os nós caíram em seguida; Nav2 reiniciado com `docker restart` ficou sem mapa; o `ros2 topic list` no robô mostrou só 2 tópicos. O `workspace/patrulha_oficial/rodar.sh` confere mapa, rede e a existência de 3 contêineres, mas não o estado dos nós.

**V5:** em 2026-11-25 o Roberto declarou a V5 de `specs/migracao-humble/` aprovada. Não há registro da medição prevista (5 min sem erro no `journalctl` do serviço `turtlebot4`): a aprovação é informação dele.

## 3. Decisões

| Ponto | Decisão |
|---|---|
| Alcance | Sobe serviços no PC com OK. Não mexe no robô (Roberto) |
| Patrulha coberta | Só `workspace/patrulha_oficial/` (Roberto) |
| Local | `.claude/skills/preflight-robo/` no repositório: carrega sem instalar e é versionada |
| Divisão | `scripts/checar.sh` faz as leituras (resultado repetível); o `SKILL.md` conduz a ordem, os pedidos de OK e o veredito |
| Falha | Item reprovado, sem resposta no prazo ou não verificado resulta em `REPROVADO` |
| Relatório | `workspace/logs/preflight_<data_hora>.md`, com a saída de cada checagem |

## 4. Limites

| Classe | Ações |
|---|---|
| Livre | Ler arquivos, `ping`, `lab.sh robo checar-rede`, `lab.sh robo estado`, ler tópicos e `get_state` num contêiner temporário `ferramentas`, ler logs |
| Com OK, um por vez | `lab.sh robo subir localizacao`, `rviz` e `nav2`; `lab.sh robo compose stop slam`; recriar o Nav2 (`robo compose rm -sf nav2` e `robo subir nav2`); `lab.sh robo parar` (avisar que derruba todos os serviços) |
| Proibido | `teleop`, `undock`, `dock`, `patrulha`, `voltar-doca`, executar o `rodar.sh`, `patrol_loop.py` sem `--verificar-localizacao`, `loop.py`, `patrol_loop2.py`, `ros2 action send_goal`, `ros2 topic pub`, `ssh` no robô, mudar rede ou configuração do robô, `sudo`, `docker restart`, `docker pause` |

Quando a correção for no robô ou exigir `sudo`, a skill mostra o comando e a página oficial, e quem roda é o operador.

## 5. Checagens, na ordem

`NS` = `/robot1`. Cada leitura tem prazo (`timeout`).

### Fase A: antes de subir qualquer coisa

| # | Checagem | Como | Passa quando |
|---|---|---|---|
| A1 | Imagens | `docker run --rm physical-ai:base printenv ROS_DISTRO`, idem `physical-ai:robo` | `humble` nas duas |
| A2 | Nada concorrendo | `infra/docker/lab.sh sim estado`; `docker ps` | Nenhum serviço do `sim`, `slam`, `teleop` ou patrulha rodando |
| A3 | Mapa | `infra/docker/lab.sh conferir workspace/mapas/mapa_lab_novo.yaml` | `UTILIZÁVEL` |
| A4 | Alcance do robô | `ping -c 5` no IP de `infra/lab/rede_lab.env` | 0% de perda; RTT anotado |
| A5 | ROS na rede | `infra/docker/lab.sh robo checar-rede` | `REDE OK`, sem aviso de bateria ou doca |
| A6 | Doca | `ros2 topic echo NS/dock_status irobot_create_msgs/msg/DockStatus --qos-profile sensor_data --once` | `is_docked: true` |
| A7 | Bateria | O mesmo para `NS/battery_state sensor_msgs/msg/BatteryState`, campo `percentage` | ≥ 0,20 (`BATERIA_BAIXA` do `patrol_loop.py`) |
| A8 | Coordenadas | Ler `DOCA` e `PONTOS` de `workspace/patrulha_oficial/upstream/patrol_loop.py` | Operador confirma os valores. Em 23/11 o arquivo voltou aos pontos antigos sem explicação |

### Fase B: subir, com OK

1. `infra/docker/lab.sh robo compose stop slam`, se estiver rodando.
2. `MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao`
3. `infra/docker/lab.sh robo subir rviz`
4. **Parada:** o operador faz o 2D Pose Estimate na pose real da doca e confirma que o laser coincide com as paredes.
5. Só depois: `MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2`

Serviço que já está rodando não é recriado sem motivo. Se o `ros2 topic list` do robô estiver incompleto, a skill mostra o `ros2 daemon stop` e `start` registrado em 23/11 para o operador rodar.

### Fase C: estabilidade, sem movimento

| # | Checagem | Passa quando |
|---|---|---|
| C1 | `ros2 service call NS/<nó>/get_state lifecycle_msgs/srv/GetState` em `map_server`, `amcl`, `controller_server`, `smoother_server`, `planner_server`, `behavior_server`, `bt_navigator`, `waypoint_follower`, `velocity_smoother` | Todos `active` |
| C2 | Repetir C1 pelo menos 60 s depois | Todos `active` |
| C3 | `lab.sh robo logs nav2` e `logs localizacao` | Sem `CRITICAL FAILURE`, `Failed to bring up` ou `no map received` depois da última subida |
| C4 | Operador atualiza o 2D Pose Estimate e a skill roda `patrol_loop.py --verificar-localizacao` no contêiner `ferramentas`, com `__ns:=/robot1` | Código de saída 0 |

C4 exige `map→odom` com menos de 2 s, e com o robô parado a transformação envelhece. Código 2 é fora da doca, 7 é sem localização, 8 é ação indisponível.

### Fase D: confirmação humana

A skill pergunta, e não presume: pessoa ao lado capaz de parar o robô; área livre; qual dos dois TurtleBots está ligado (etiqueta ou número de série); o trajeto de volta à doca está livre no costmap do RViz.

### Saída

Tabela item, resultado, evidência; veredito; caminho do relatório. Com `APROVADO`, mostra `workspace/patrulha_oficial/rodar.sh 1` para o operador rodar, lembrando de refazer o 2D Pose Estimate no prompt dele. O veredito vale para aquele momento e não autoriza movimento.

## 6. Passos de implementação

- [ ] Registrar a V5 como declarada pelo Roberto e atualizar os avisos que mandam não usar o `lab.sh robo`: `docs/contexto/AGENTES.md`, `docs/guias/como-rodar.md`, `docs/guias/como_rodar_patrol_loop.md`, `specs/patrol-inf/kit-de-campo.md`, `infra/compose/robo.yaml`
- [ ] Robô desligado: testar cada comando das Fases A e C e anotar a saída real
- [ ] Robô ligado e na doca: conferir os comandos na documentação oficial ([Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html), [Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html), [Docking](https://iroboteducation.github.io/create3_docs/api/docking/)) e rodar um a um
- [ ] Escrever `scripts/checar.sh` e `SKILL.md`
- [ ] Rodar os critérios da seção 7
- [ ] Documento em `docs/tarefas/`, linha na tabela e `python3 infra/ferramentas/checar_caminhos.py`

## 7. Critérios de pronto

| # | Teste | Resultado esperado |
|---|---|---|
| P1 | Sessão nova do `claude` na raiz, digitar `/` | `preflight-robo` na lista |
| P2 | Robô desligado | `REPROVADO` em A4; nenhum serviço sobe |
| P3 | Rodar o comando abaixo da tabela na pasta da skill | Só linhas que detectam `teleop` em A2 |
| P4 | Negar o OK na Fase B | `docker ps` igual antes e depois; `REPROVADO` |
| P5 | Robô na doca, tudo certo | `APROVADO`; `is_docked: true` antes e depois; o robô não se move |
| P6 | Parar a `localizacao` (com OK) e rodar de novo, negando a subida | `REPROVADO`, citando o item |

Comando do P3:

```bash
grep -nE 'teleop|undock|send_goal|topic pub|voltar-doca|rodar\.sh|ssh |sudo|docker (restart|pause)' scripts/checar.sh
```

## 8. A verificar no laboratório

- `--field` e `--once` do `ros2 topic echo` nos tópicos do robô.
- Se o `get_state` responde pelo Discovery Server a partir do `ferramentas` (em 21/11 levou cerca de 7 s).
- Se subir o Nav2 publica algo em `NS/cmd_vel` sem meta enviada (a CLI não enxergou o tópico em 23/11).
- Se construir o `TurtleBot4Navigator` em C4 publica algo no robô.
- Se `ipc: host` com um contêiner temporário afeta os heartbeats do Nav2 (a hipótese de 23/11 sobre memória compartilhada não foi confirmada).

## 9. Fora do escopo

Mover o robô; diagnosticar a causa de uma falha do Nav2; a `patrulha_tb4`; corrigir `rodar.sh`, `lab.sh` ou o `patrol_loop.py`.

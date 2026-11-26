# SPEC: reformulação enxuta do repositório depois da task 1

**Status:** Aprovada em 2026-11-26 (portão da skill `/sdd`, no plano da sessão). Implementada na branch `refactor/reformulacao-task1`; falta a validação no robô (seção 6)
**Rigor:** spec leve com inventário, como a de 2026-11-18 (na tag `task1-concluida`: `docs/historico/spec-enxugamento.md`)
**Antes:** tag `task1-concluida` (commit `ef1ee79`)

## 1. Objetivo

O repositório tem só o que a patrulha e os comandos por LLM usam no TurtleBot 4, no estilo do repositório de um colega que entrega as mesmas missões (`github.com/vidal56/My_Turtle`):

- scripts Python soltos;
- um script bash curto por tarefa;
- uma imagem Docker.

O que já custou depuração no robô continua funcionando (seção 4).

## 2. Contexto

| Parte | Antes (`task1-concluida`) | Colega |
|---|---|---|
| LLM | 39 arquivos, 3.359 linhas (`missao.py` 412, ensaios 620, 64 testes) | 4 arquivos, 369 linhas |
| Execução | `lab.sh` 415 + compose 423 + Docker 311 + `rodar.sh` e `checar.sh` 195 | 8 scripts (99) + Docker (19) |
| Patrulha | 3 scripts (509), com o núcleo duplicado | 1 script por rota |
| Nav2 | 2 launches nossos, um deles cópia de 276 linhas do `navigation_launch.py` | launch oficial |
| Legado | `patrulha_tb4` v1, L1, loopback, Gazebo maze, specs cumpridas | nenhum |

**Decisões do Roberto (2026-11-26):**

| Ponto | Decisão |
|---|---|
| Patrulha | `patrulha.py` com subcomandos `voltas N`, `ida-e-volta`, `continuo` (e `doca`, o `--voltar-doca` de antes) |
| Simulação | Sai toda (ADR-003) |
| Execução | Sem colcon nem compose (ADR-004) |
| LLM | Ficam o "pare" no trajeto, as recusas por frase, a avaliação de frases e o freio. Saem as coordenadas livres, a máquina de estados e os ensaios com robô falso (ADR-005) |
| Testes | Mínimo: `tests/test_llm.py`. CI com ruff e pytest |

## 3. Estrutura

```text
README.md            como rodar e o mapa das pastas
docker/Dockerfile    imagem única (ros:humble-ros-base + TurtleBot 4 + RViz)
scripts/             env, checar, subir, parar, patrulha, llm, falar, mapa, teleop
launch/              localizacao e nav2: o launch oficial + bond_timeout=120
config/              parâmetros da localização e do Nav2 (os de antes)
mapas/               mapa_lab_novo e os pontos medidos
robo.py              DOCA, PONTOS e o núcleo (doca, localização, servidores, navegar, voltar)
patrulha.py          voltas N | ida-e-volta | continuo | doca
llm/                 interpretar.py (sem ROS), no_llm.py, falar.py, prompt.txt, avaliar.py,
                     frases.json
tests/test_llm.py    regras, conferência da resposta, bateria e pontos
docs/  specs/  .claude/  .github/
```

## 4. Não perder

| O quê | Antes | Agora |
|---|---|---|
| `bond_timeout=120` (AMCL e Nav2 caíam com 4 s) | `localization_inf.launch.py`, cópia `navigation_inf.launch.py` | `launch/*.launch.py` com `SetParameter` |
| Remapeamento do `scan` dos costmaps no namespace | `nav2_inf.launch.py` | Já feito pelo `nav2.launch.py` oficial, que o nosso inclui |
| Nav2 a 0,15 m/s e tempos de descoberta do lab | `nav2_inf_devagar.yaml` | `config/nav2.yaml` (mesmo conteúdo) |
| Discovery Server, id, namespace, IP; RMW e UDPv4; `--network host`, `--ipc host` | `infra/lab/*`, `robo.yaml` | `scripts/env.sh` |
| Rotas 192.168.185/186 pelo robô | `lab.sh` (`checar_rotas`, `usar`) | `scripts/checar.sh` avisa e mostra o `nmcli` (hipótese H1 em aberto) |
| Um controlador por vez | `rodar.sh`, `lab.sh` | `patrulha.sh` e `llm.sh mover` |
| Pontos e doca medidos | `patrol_loop.py:27-34` | `robo.py`, conferidos por teste |
| Dock/undock por regra, negação e sequência recusadas, "pare" sem o modelo | `interpretador.py` | `llm/interpretar.py` (as mesmas regex) |
| Bytes soltos do terminal e `stty iutf8` | `entrada.py`, serviço `falar` | `llm/falar.py`, `scripts/falar.sh` |
| `map_saver_cli` com o `/map` remapeado | `lab.sh salvar` | `scripts/mapa.sh salvar` |
| `stamped:=false` e 0,15 m/s no teleop | serviço `teleop` | `scripts/teleop.sh` |

**Uma mudança de comportamento:** o rclpy deixou de tratar os sinais (`robo.iniciar_ros`). Antes, o Ctrl+C na patrulha derrubava o contexto do ROS antes do `cancelTask()`. Agora Ctrl+C e `docker stop` cancelam a meta com o ROS ainda de pé, e isso vale para a patrulha e para o LLM.

## 5. Inventário

| Antes | Destino |
|---|---|
| `workspace/patrulha_oficial/{patrol_loop,patrol_loop2,loop}.py`, `rodar.sh` | `robo.py`, `patrulha.py` e `scripts/patrulha.sh` |
| `workspace/meu_ws/src/llm_tb4/**` | `llm/` e `tests/test_llm.py`. Saem `missao.py`, `execucao.py`, `coordenadas.py`, `mapa.py`, `pontos.py`, `recursos.py`, `entrada.py`, os ensaios e o pacote colcon |
| `workspace/meu_ws/src/patrulha_tb4/**` | Ficam os YAMLs da localização e do Nav2 (`config/`) e o launch da localização (`launch/`). O resto sai: patrulha v1, `nav2_inf`, a cópia do `navigation_launch`, `mapa_slam`, configs e testes |
| `workspace/meu_ws/src/lab_tb4/**`, `terceiros/**` | Saem |
| `workspace/mapas/` | `mapas/` (sem `patrulha_mapa_lab_novo.yaml`, que era da v1) |
| `infra/**` | `docker/Dockerfile` e `scripts/` |
| `.claude/skills/preflight-robo/` | Fica, chamando `scripts/checar.sh` |
| `specs/{patrol-inf,migracao-humble,llm-integracao,preflight-robo}`, `docs/historico/` | Saem (estão na tag) |
| `docs/guias/` | `como-rodar.md`, `llm.md` e `acesso-ao-robo.md` |
| `docs/tarefas/`, `docs/decisoes/` | Ficam. ADR-002 substituído; entram os ADR-003 a 005 |

## 6. Pronto quando

**No notebook:**

1. `ruff check .` e `pytest tests/` passam.
2. `bash -n scripts/*.sh` passa.
3. `git grep -nE "workspace/|infra/|patrulha_tb4|llm_tb4|lab_tb4|patrol_loop|parking_brake|lab\.sh" -- ':!docs/tarefas' ':!specs/reformulacao-task1' ':!docs/decisoes'` volta vazio.

**No PC do lab (o Roberto; ação que move o robô só com o OK dele):**

4. `docker build -t physical-ai docker/`, e depois `scripts/checar.sh` dá APROVADO.
5. `scripts/subir.sh`, 2D Pose Estimate e `scripts/subir.sh nav2`. Depois, `ros2 param get <ns>/lifecycle_manager_navigation bond_timeout` dá 120.0. Se não der, `launch/nav2.launch.py` volta a incluir a cópia do `navigation_launch.py` (na tag).
6. `scripts/patrulha.sh --verificar-localizacao voltas 1`, e depois `scripts/patrulha.sh voltas 1`.
7. `scripts/llm.sh` com 5 frases no `scripts/falar.sh`. Depois, `scripts/llm.sh mover`, um ponto e um "pare" no trajeto.
8. `python3 llm/avaliar.py` no PC, comparado aos números de 25/11 (`docs/tarefas/2026-11-25-llm-fase-1.md`).

`ida-e-volta`, `continuo` e `doca` seguem sem ensaio físico, como antes.

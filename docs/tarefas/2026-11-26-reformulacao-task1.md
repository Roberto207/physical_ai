# 2026-11-26: tag da task 1, reformulação enxuta e brainstorm da task 2

**Resposta direta:**

- O estado entregue da task 1 está na tag anotada `task1-concluida` (commit `ef1ee79`, já no GitHub).
- Na branch `refactor/reformulacao-task1`, o repositório foi de 212 para 100 arquivos versionados.
- O código e os scripts foram de 9.882 para 1.096 linhas (contando `.py`, `.sh`, Dockerfile e compose; sem os YAMLs de parâmetros, mapas, `.claude/` e CI).
- A patrulha e o LLM fazem o mesmo que antes, com quatro exceções:
  - as coordenadas livres saíram, por decisão do Roberto;
  - Ctrl+C e `docker stop` passaram a cancelar a meta de verdade;
  - o "pare" passou a cancelar também o dock e o undock iniciados pelo LLM;
  - a patrulha ganhou o modo `doca`, que é o `--voltar-doca` de antes.

**O que falta:** nada foi rodado no robô nem no PC do lab. A checklist está na seção 6 da spec.

## Por que

O repositório de um colega (`github.com/vidal56/My_Turtle`) entrega as mesmas missões com 4 arquivos de LLM (369 linhas) e 8 scripts bash (99 linhas). O nosso tinha 39 arquivos só no LLM (3.359 linhas) e um `lab.sh` de 415 linhas. Também carregava a patrulha v1, o simulador leve L1, o Gazebo maze e specs já cumpridas. Spec: `specs/reformulacao-task1/SPEC.md`. Decisões: ADR-003 (sem simulação até a task 2), ADR-004 (sem colcon) e ADR-005 (LLM em JSON).

## O que foi feito, onde e para quê

| Arquivo | Para que serve | De onde veio |
|---|---|---|
| `robo.py` | `DOCA` e `PONTOS` (única fonte) e o núcleo: esperar doca, localização e servidores, `navegar` (com cancelamento), `voltar_doca`, sinais | As funções repetidas em `patrol_loop.py` e `loop.py` |
| `patrulha.py` | `voltas N`, `ida-e-volta`, `continuo` e `doca`. Cada modo é só uma lista de pernas (ponto, para onde olhar, nome) | `patrol_loop.py`, `patrol_loop2.py` e `loop.py` |
| `llm/interpretar.py` | Regras (parar, negação, sequência, dock/undock), Ollama com JSON Schema e conferência. Sem ROS | `interpretador.py` e `validar_acao.py`, sem as coordenadas |
| `llm/no_llm.py` | Nó ROS: fila de mensagens, freio, execução pelo `robo.py`, dock e undock canceláveis | Substitui `no_linguagem_natural.py`, `missao.py` (412 linhas) e `execucao.py` |
| `llm/falar.py`, `prompt.txt`, `avaliar.py`, `frases.json` | Terminal de pedidos; prompt sem a ação de coordenadas; avaliação com as 388 frases dos 8 conjuntos de 25/11 | `falar.py`, `entrada.py`, `comandos.txt`, `test/frases/*.json` |
| `scripts/*.sh` | `env` (robô e `docker run` comum), `checar`, `subir` e `subir nav2`, `parar`, `patrulha`, `llm`, `falar`, `mapa`, `teleop`, `ros` | `lab.sh`, `robo.yaml`, `rodar.sh`, `infra/lab/*` |
| `launch/nav2.launch.py` | Inclui o `nav2.launch.py` oficial do TurtleBot 4 e põe `bond_timeout=120` com `SetParameter` | Substitui `nav2_inf.launch.py` e a cópia de 276 linhas do `navigation_launch.py` |
| `docker/Dockerfile` | Imagem única: Humble, TurtleBot 4, Nav2, SLAM, RViz, teleop | 4 estágios (`base`, `robo`, `sim`, `llm`) |
| `tests/test_llm.py` | 50 testes sem ROS: regras, resposta do modelo, bateria, prompt, frases e os pontos iguais aos da tag | 64 testes, 40 deles da máquina de estados |
| `.github/workflows/ci.yml` | `ruff` e `pytest tests` | 5 jobs |
| `specs/multi-robos/BRAINSTORM.md` | O desafio dos três robôs, o bloqueio das rotas, a hipótese H1, SSH vs. DDS, 4 arquiteturas | Pesquisa desta tarefa |

**Saíram** (estão na tag):

- `workspace/` inteiro: `patrulha_tb4`, `lab_tb4`, `nav2_loopback_sim`, `llm_tb4`, `patrulha_oficial`;
- `infra/`;
- quatro specs: `patrol-inf`, `migracao-humble`, `llm-integracao`, `preflight-robo`;
- `docs/historico/`;
- quatro guias, substituídos por `docs/guias/como-rodar.md` e `docs/guias/llm.md`.

As sobras locais de `workspace/` e `infra/` (só caches e build do colcon) foram apagadas do disco.

### Detalhes que mudam o comportamento

- **Sinais:** `robo.iniciar_ros()` inicia o rclpy com `SignalHandlerOptions.NO` e converte SIGTERM em `KeyboardInterrupt`. Com o tratador padrão do rclpy, o Ctrl+C derrubava o contexto antes do `cancelTask()` do `except`, e a meta podia continuar ativa no Nav2. O nó LLM antigo já fazia isso; a patrulha antiga não fazia.
- **Dock e undock no LLM:** o `dock()` do `TurtleBot4Navigator` bloqueia até terminar. O nó novo usa `dock_send_goal()` e `isDockComplete()` num laço, e cancela pelo `goal_handle` quando chega um "pare". Isso segue a regra de 25/11 ("só pare cancela a manobra").
- **Subida em duas etapas:** `scripts/subir.sh` sobe a localização e o RViz, e `scripts/subir.sh nav2` sobe o Nav2. É a ordem que funcionou no robô em 25/11.
- **Rotas:** `scripts/checar.sh` só avisa e mostra o `nmcli`. A troca automática do `lab.sh robo usar` saiu. Se a hipótese H1 se confirmar, as rotas deixam de ser necessárias.

## Como foi verificado (no notebook, sem ROS)

- `ruff check .` (0.17.3): sem avisos.
- `python3 -m pytest tests`: 50 passaram.
- `bash -n scripts/*.sh`: sem erro.
- **Rotas da patrulha:** comparei as pernas e o parser de `patrulha.py` com os três scripts antigos, com o ROS simulado por módulos falsos. As sequências de pontos e "olhar para" são iguais, e as opções inválidas são recusadas.
- **Pontos:** o teste compara `DOCA` e `PONTOS` com os valores de `patrol_loop.py` da tag.
- **Nav2 oficial:** li o `nav2.launch.py` do `turtlebot4_navigation` (ramo humble no GitHub). Ele já faz o namespace, os dois `SetRemap` do scan e `use_composition=False`, que era o que o `nav2_inf.launch.py` reproduzia.
- **Citações:** `git grep` não acha citação de caminho apagado fora dos documentos históricos.

**Não verificado:**

- nada rodou com ROS, Docker ou o robô;
- a imagem nova não foi construída (o notebook não tem Docker e tem 7,4 GiB);
- o `bond_timeout` pelo launch oficial;
- o cancelamento de dock e undock;
- `avaliar.py` com o modelo real;
- `scripts/mapa.sh salvar`.

## Efeito prático

Para usar a branch no PC do lab:

```bash
git fetch && git switch refactor/reformulacao-task1
docker build -t physical-ai docker/
```

Depois, siga `docs/guias/como-rodar.md` e marque a seção "Reformulação de 26/11" de `docs/contexto/pendencias.md`. Com o robô validado, abra o PR para `main`. Se algo quebrar, `git switch main` (ou `git checkout task1-concluida`) volta à estrutura anterior, que usava as imagens `physical-ai:base` e `:robo`.

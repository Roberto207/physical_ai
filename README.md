# Physical AI: patrulha e LLM no TurtleBot 4

Projeto AKCIT (INF-UFG). A equipe tem duas missões no TurtleBot 4 real, com ROS 2 Humble:

- **patrulha**: rondar os pontos do mapa e voltar à doca;
- **comandos por LLM**: o robô vai aonde o pedido em português manda.

Tudo roda no PC do laboratório, em Docker, e conversa com o robô pelo Wi-Fi. O estado em que a task 1 foi entregue está na tag `task1-concluida`.

## Como rodar (no PC do lab)

```bash
docker build -t physical-ai docker/       # uma vez (ou depois de mudar o Dockerfile)
export ROBO=robot3                         # robot1 (padrão) ou robot3
scripts/checar.sh                          # rede e tópicos do robô: precisa dar APROVADO
scripts/subir.sh                           # localização + RViz → 2D Pose Estimate na doca
scripts/subir.sh nav2                      # Nav2
scripts/patrulha.sh voltas 1               # MOVE O ROBÔ: patrulha (ou ida-e-volta, continuo, doca)
scripts/llm.sh                             # LLM com freio (não move); "scripts/llm.sh mover" move
scripts/falar.sh                           # outro terminal: escrever os pedidos ao LLM
scripts/parar.sh                           # encerra tudo
```

Passo a passo, sinais de que cada etapa subiu e o que fazer quando falha: `docs/guias/como-rodar.md`. O LLM tem guia próprio: `docs/guias/llm.md`.

## Mapa das pastas

```text
robo.py             pontos do mapa (DOCA, PONTOS) e o núcleo comum: doca, localização, navegar
patrulha.py         a patrulha: voltas N | ida-e-volta | continuo | doca
llm/                nó do LLM (no_llm.py), regras e Ollama (interpretar.py), terminal (falar.py),
                    prompt.txt e avaliação (avaliar.py, frases.json)
scripts/            um script por tarefa no PC do lab; env.sh escolhe o robô
launch/ config/     localização e Nav2: os launches oficiais com os ajustes do lab
mapas/              mapa em uso e os pontos medidos
docker/             a imagem (ROS 2 Humble + TurtleBot 4 + RViz)
tests/              testes sem ROS (CI)
docs/               contexto, guias, decisões (ADRs) e um documento por tarefa
specs/              specs (ver specs/README.md)
.claude/            skills e subagentes do Claude Code
```

## Testes

| Onde | O quê |
|---|---|
| Notebook e CI | `ruff check .` e `python3 -m pytest tests` (sem ROS) |
| PC do lab, sem mover | `scripts/patrulha.sh --verificar-localizacao voltas 1`; `scripts/llm.sh` (freio) |
| Robô | O resto, sempre com uma pessoa ao lado (`docs/contexto/AGENTES.md`, seção 1) |

Regras para agentes de IA: `docs/contexto/AGENTES.md`. Em aberto: `docs/contexto/pendencias.md`.

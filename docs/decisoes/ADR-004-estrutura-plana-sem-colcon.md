# ADR-004: Estrutura plana, sem pacotes colcon

**Status:** Aceito em 2026-11-26 (portão da spec `specs/reformulacao-task1/`)
**Data:** 2026-11-26

## Contexto

O repositório tinha 3 pacotes ROS compilados a cada subida de contêiner, um `lab.sh` de 415 linhas e 423 linhas de compose. O repositório de um colega entrega as mesmas missões com scripts Python soltos e 8 scripts bash curtos.

## Decisão

Os programas são scripts Python na raiz (`patrulha.py`, `robo.py`, `llm/`), executados com `python3 <arquivo> --ros-args -r __ns:=<ns>`. Os launches nossos rodam por caminho (`ros2 launch /work/launch/...`). Uma imagem (`docker/Dockerfile`) e um script por tarefa em `scripts/`, com `docker run`.

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| Compose enxuto e pacotes menores | Mantém a compilação na subida e uma camada a mais |

## Consequências

### Positivas

- Mudar código não pede compilação nem imagem nova.
- O robô e a rede ficam num só arquivo (`scripts/env.sh`).

### Negativas

- Sem `ros2 run`; os imports entre scripts usam o caminho do repositório.

### Mitigação

- O repositório entra no contêiner sempre em `/work`.

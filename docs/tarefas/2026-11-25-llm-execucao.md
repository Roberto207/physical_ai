# LLM: código de execução

**Data:** 2026-11-25

**Resposta direta:** o nó `llm_tb4` passou a executar os pedidos com o `TurtleBot4Navigator`, com o freio ligado por padrão. Foi ensaiado só com um robô falso, sem rede. Não rodou no simulador nem no robô.

## O que foi feito

| Arquivo | O que é |
|---|---|
| `workspace/meu_ws/src/llm_tb4/llm_tb4/missao.py` | Regras de mover, cancelar e ignorar, sem ROS |
| `workspace/meu_ws/src/llm_tb4/llm_tb4/execucao.py` | Clientes de ação, sensores, cancelamento |
| `workspace/meu_ws/src/llm_tb4/llm_tb4/pontos.py` | Lê os pontos de `workspace/patrulha_oficial/patrol_loop.py` |
| `workspace/meu_ws/src/llm_tb4/llm_tb4/falar.py` | Terminal de conversa |
| `infra/compose/robo.yaml`, `infra/docker/lab.sh` | `lab.sh robo llm` e `falar`; exclusão com patrulha e controle manual; `parar` encerra o nó primeiro |
| `workspace/patrulha_oficial/rodar.sh`, `.claude/skills/preflight-robo/scripts/checar.sh` | Também recusam o nó llm rodando |

Comportamento, desvios e limites: `specs/llm-integracao/PLANO.md`. Antes do código houve uma revisão do desenho por um subagente, que apontou as esperas sem prazo e o falso sucesso dos atalhos do navegador.

## Defeitos achados pelos ensaios e corrigidos

| Defeito | Correção |
|---|---|
| O terminal `falar` segurava o teclado esperando confirmação, atrasando o "pare", e abortava ao sair | Sem espera; encerramento em ordem |
| No `docker stop`, o `ros2 launch` morria e o nó saía sem cancelar a meta | O serviço executa o nó direto |
| Fechar o terminal do `compose run` deixava o contêiner vivo e o robô andando | Um vigia no `lab.sh` para o nó |

## Verificação (nada alcançou o robô)

- `llm_tb4`: 233 testes sem ROS; `flake8` limpo.
- `test/ensaio_execucao.py`: 39 verificações; `test/ensaio_no.py`: 20; sem falhas.
- Serviço do robô num contêiner sem rede, com robô falso: `docker stop`, `Ctrl+C` e `SIGHUP` cancelaram a meta.
- `lab.sh` com Compose falso, num terminal virtual: fechar o terminal, `Ctrl+C` e matar o script cancelaram a meta.
- Recusas do `lab.sh` e do `rodar.sh` com `docker` falso.

## O que não foi verificado

Nav2 real, simulador, robô, comunicação pelo Discovery Server, cancelamento do dock na Create 3, `shellcheck`.

# LLM: pacote `llm_tb4` e nó sem movimento

**Data:** 2026-11-25

**Resposta direta:** o interpretador virou o pacote ROS `llm_tb4`, com um nó que segue o `natural_language_nav` do tutorial oficial, aceita coordenadas livres, `dock` e `undock`, e atende "parar" mesmo ocupado. Não há código de movimento.

## Ensaios antes de implementar

| Ideia | Ensaio | Resultado |
|---|---|---|
| Quem lê as coordenadas | 18 frases, modelo contra código | Código 18/18; modelo 16/18, inventando números. Escolhido o código; 18/19 em frases novas |
| Prompt com as ações novas | Todos os conjuntos numa cópia | `undock` virou `encaixar`; criada regra por código para `dock`/`undock` |
| Nó que atende "parar" ocupado | 20 verificações num contêiner sem rede, com Ollama falso | Achou erro ao encerrar com `Ctrl+C`; corrigido antes de entrar no projeto |
| Isolamento do robô | Contêiner com a rede do PC, robô ligado | O nó só viu os próprios tópicos e respondeu com o modelo real |

## Mudanças

| Antes | Depois |
|---|---|
| `workspace/llm/` | `workspace/meu_ws/src/llm_tb4/` (o CI foi ajustado) |
| | `infra/compose/llm.yaml`: nó isolado, domínio 43, só na máquina |
| | `specs/llm-integracao/PLANO.md` com o que segue o tutorial e os desvios |

Também: pacote do `TurtleBot4Navigator` corrigido em `docs/contexto/stack.md`, e o comentário do alvo `llm` do Dockerfile.

## Verificação, a partir do repositório

- `llm_tb4`: 176 testes; `test/ensaio_no.py`: 20 verificações sem falha; `lab_tb4`: 17.
- Compose: pedidos publicados com o comando do README, decisões conferidas no log, só os tópicos do nó visíveis.
- Medição com o modelo real no plano.
- `patrulha_tb4`: 156 aprovados e 1 reprovado, o mesmo das pendências.

**Não verificado:** execução (não existe), simulador, robô, CI no GitHub, tempo com o robô e o RViz competindo por CPU.

## Interpretação do pedido

"Seguiremos com o aceita coordenadas livres" foi lido como a linha inteira do tutorial: coordenadas, `dock` e `undock`. Os demais desvios ficaram como estão e precisam de decisão antes da execução.

## Decisões e guia (mesmo dia)

- Não haverá aprovação por ação. Mensagem durante o trajeto cancela a meta e vira a ordem principal. Registrado em `specs/llm-integracao/PLANO.md` e `docs/decisoes/README.md`; **ainda não implementado**.
- Guia de execução: `docs/guias/llm-linguagem-natural.md`, ligado a partir do `como-rodar.md` e do `README.md`.

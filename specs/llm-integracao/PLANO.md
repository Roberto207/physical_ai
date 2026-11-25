# Plano: integração com LLM no TurtleBot 4

**Data:** 2026-11-25. **Estado:** interpretador e nó sem movimento feitos; execução proposta, a aprovar.

## Objetivo

Receber um pedido em português ("vá até a geladeirinha"), traduzi-lo para uma ação conhecida e, só com autorização, executá-la com o Nav2. O modelo é local: Ollama com `qwen2.5:1.5b`. Código em `workspace/meu_ws/src/llm_tb4`.

## Base oficial

| Fonte | O que usamos |
|---|---|
| [Manual, TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) | Seção de integração com LLM. Os exemplos são feitos para simulação; no robô físico exigem destinos e mapa próprios |
| [`natural_language_nav.py`](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_openai_tutorials/turtlebot4_openai_tutorials/natural_language_nav.py) | Desenho do nó |
| [`turtlebot4_api.txt`](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_openai_tutorials/prompts/turtlebot4_api.txt) | Prompt em arquivo, com exemplos |
| [Ollama: chat](https://docs.ollama.com/api/chat) e [saída estruturada](https://docs.ollama.com/capabilities/structured-outputs) | Chamada local, esquema JSON em `format`, esquema repetido no prompt, temperatura 0 |

## O que segue o tutorial

| Item | Situação |
|---|---|
| Pacote `ament_python` com `package.xml` e `setup.py` | Feito |
| Launch `natural_language_nav_launch.py` e executável `natural_language_nav` | Feito |
| Prompt instalado no pacote | Feito |
| Tópicos `user_input` e `ready_for_input` | Feito |
| Parâmetros `model_name` e `parking_brake` (ligado por padrão) | Feito; com o freio desligado o nó não inicia, porque não há movimento |
| Ocupado, o nó ignora novos pedidos | Vale enquanto interpreta, exceto "parar". Durante o trajeto muda (ver desvios) |
| Coordenadas livres com direção, `dock` e `undock` | Feito na interpretação (decisão do operador) |
| `TurtleBot4Navigator` (`dock`, `undock`, `startToPose`) | Na fase de execução |

## Desvios

| Desvio | Motivo | Decisão |
|---|---|---|
| Ollama local no lugar da API da OpenAI | Gratuito | Aceito pelo operador |
| "Parar" atendido mesmo com o nó ocupado | Poder interromper | Aceito pelo operador |
| JSON por esquema e validador no lugar de `exec()` | O modelo erra e o código rodaria direto | Em uso; confirmar antes da execução |
| Sem dock e pose `[0, 0]` automáticos na partida | Usamos 2D Pose Estimate; a doca não está em `[0, 0]` | A confirmar antes da execução |
| Mensagem durante o trajeto cancela a meta e vira a ordem principal | Poder interromper e corrigir | Aceito pelo operador (25/11); falta implementar |
| Locais por nome (`destinos.json`), voltar à doca e parar | Nosso mapa e segurança | Em uso |
| Coordenada conferida no mapa; bateria mínima de 20% para sair | Não mandar o robô para onde o mapa não permite | Em uso |
| Coordenadas e `dock`/`undock` lidos por código | O modelo inventou números e trocou `undock` por `dock` nos ensaios | Em uso |
| Nó `llm_node`, pacote `llm_tb4`, parâmetros `ollama_url`, `mapa` e `bateria_simulada`, namespace `/robot1` | Configuração do projeto | Em uso |

## Fases

| Fase | Entrega | Critério para avançar | Estado |
|---|---|---|---|
| 1 | Interpretador, testes e medição | Testes sem modelo passam; erros medidos | **Feita** |
| 2 | Plano alinhado ao tutorial | Desvios listados | **Feita** |
| 3 | Pacote e nó sem código de movimento, isolado do robô | `test/ensaio_no.py` sem falhas | **Feita** |
| 4 | Execução no simulador, com confirmação do operador | Ir, parar e voltar à doca observados | Proposta; o simulador é do operador |
| 5 | Robô real, supervisionado | Autorização e fase 4 aprovada | Proposta |

## Requisitos da execução (fases 4 e 5)

Decisões do operador em 25/11:

- **Sem aprovação por ação.** O que passar pela validação é executado, como no tutorial com o freio desligado.
- **Toda mensagem recebida durante o trajeto cancela a meta atual e passa a ser a ordem principal.**

Como o item acima será implementado (interpretação nossa, a confirmar no teste):

- O cancelamento acontece **na chegada** da mensagem, antes de consultar o modelo.
- Se a nova mensagem não virar uma ação válida, o robô fica parado.

Demais requisitos:

- Acompanhar a meta sem bloquear a recepção. A função `navegar` de `workspace/patrulha_oficial/patrol_loop.py` bloqueia até o fim; dock e saída da doca não são canceláveis do mesmo modo, e o comportamento nesses casos precisa ser definido e testado.
- Reaproveitar de `patrol_loop.py` os pontos, a espera por `map→odom` e a volta à doca. Sair da doca antes de navegar. Definir a direção quando o pedido não disser.
- Um controlador por vez: nunca junto de um programa de patrulha.
- Bateria real do `battery_state`.
- O texto não substitui a parada física: pessoa ao lado em todo teste no robô.

## Decisão em aberto: onde o modelo é consultado no simulador

O Ollama escuta só em `127.0.0.1`. O nó roda com a rede do PC e o alcança (`infra/compose/llm.yaml`). Os contêineres do simulador usam rede isolada (`infra/compose/sim.yaml`) e não alcançam. Opções: entregar ao simulador só a ação já validada; ou configurar o Ollama para escutar também na ponte do Docker.

O Gazebo não tem um mundo igual ao `mapa_lab_novo`. O simulador leve aceita um mapa pela variável `MAPA`; com este mapa ainda não foi testado.

## Aprovação humana

O manual e o `natural_language_nav.py` **não preveem aprovação de cada ação**. A única trava é o `parking_brake`: ligado, nada é executado; desligado, o código escrito pelo modelo é executado na hora com `exec()`. Em caso de erro, o nó só registra a falha.

**Decisão (25/11): não haverá aprovação por ação.** Consequência registrada: uma interpretação errada move o robô até chegar outra mensagem ou alguém pará-lo. As proteções que restam são a validação (ações conhecidas, coordenada no mapa, bateria), o cancelamento por nova mensagem e a pessoa ao lado.

## Medição (25/11, CPU do PC do laboratório)

Mediana de cerca de 0,55 s por pedido que passa pelo modelo.

| Conjunto (`test/frases/`) | Acertos | Moveria errado | Parar não reconhecido | Observação |
|---|---|---|---|---|
| `ajuste.json` | 17/18 | 0 | 0/2 | Usado para ajustar |
| `reserva.json` | 13/14 | 0 | 0/2 | |
| `estresse.json` | 12/16 | 4 | | Frases capciosas |
| `locais.json` | 18/21 | 2 | | Nomes dos locais |
| `avaliadores.json` | 206/265 | **51** | 3/94 | Frases de um avaliador para quebrar o sistema; as regras de parar foram ajustadas nelas |
| `parar_reserva.json` | 14/24 | 0 | **10/20** | Formas de parar novas |
| `novas_acoes.json` | 19/20 | 1 | | Coordenadas, dock e undock; as regras de dock foram ajustadas nele |
| `acoes_reserva.json` | 16/18 | 2 | | Escrito depois; erros em pergunta e afirmação |

Três coordenadas marcadas como válidas nos dois últimos conjuntos foram corrigidas para recusa: ficam perto de obstáculo no mapa.

Com o prompt das ações novas, em relação ao anterior: `avaliadores` caiu de 66 para 51 movimentos errados; `ajuste` perdeu um acerto ("vai lá perto do frigobar" passou a ser recusado), `locais` um e `parar_reserva` um.

**Leitura:** perguntas, condições e afirmações ainda podem virar ação, e a lista de formas de parar não generaliza. Por decisão do operador, as regras de interpretação não ficaram mais rígidas e não haverá aprovação por ação. Durante o trajeto, o cancelamento por qualquer mensagem passa a cobrir as formas de parar que a lista não conhece. As amostras vêm de poucas fontes e não representam o uso real.

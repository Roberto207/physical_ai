# Plano: integração com LLM no TurtleBot 4

**Data:** 2026-11-25. **Estado:** fase 1 feita; fases seguintes propostas, a aprovar.

## Objetivo

Receber um pedido em português ("vá até a geladeirinha"), traduzi-lo para uma ação conhecida e, só com autorização, executá-la com o Nav2. O modelo é local: Ollama com `qwen2.5:1.5b`.

## Base oficial

| Fonte | O que usamos |
|---|---|
| [Manual, TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) | Seção de integração com LLM. Os exemplos são feitos para simulação; no robô físico exigem destinos e mapa próprios |
| [`natural_language_nav.py`](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_openai_tutorials/turtlebot4_openai_tutorials/natural_language_nav.py) | Desenho do nó |
| [`turtlebot4_api.txt`](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_openai_tutorials/prompts/turtlebot4_api.txt) | Prompt em arquivo, com exemplos |
| [Ollama: chat](https://docs.ollama.com/api/chat) e [saída estruturada](https://docs.ollama.com/capabilities/structured-outputs) | Chamada local, esquema JSON em `format`, esquema repetido no prompt, temperatura 0 |

## O que seguimos e o que trocamos

| Exemplo oficial | Aqui | Motivo |
|---|---|---|
| Tópicos `user_input` e `ready_for_input` | Manter | Interface documentada |
| Parâmetros `model_name` e `parking_brake` (ligado por padrão) | Manter | Teste sem movimento |
| `TurtleBot4Navigator` (`dock`, `undock`, `startToPose`) | Manter | Já é a base da nossa patrulha |
| Prompt em arquivo e dicionário de destinos | Manter, em `workspace/llm/` | |
| API da OpenAI (paga) | Ollama local | Gratuito |
| `exec()` no código escrito pelo modelo | JSON por esquema + `validar_acao.py` | O modelo não escreve código |
| Dock, pose inicial `[0, 0]` e undock automáticos na partida | Não fazer | Nosso mapa usa 2D Pose Estimate |
| Nomes sem namespace | `/robot1` no robô | Configuração do nosso robô |

## Fases

| Fase | Entrega | Critério para avançar | Estado |
|---|---|---|---|
| 1 | Interpretador em Python puro (`workspace/llm/interpretador.py`), testes e medição | Testes sem modelo passam; erros medidos e registrados | **Feita** |
| 2 | Nó ROS com `user_input`, `ready_for_input` e `parking_brake`, **sem código de movimento** | Recebe frases e registra a decisão | Proposta |
| 3 | Execução no simulador leve, com confirmação do operador | Ir, parar e voltar à doca observados | Proposta |
| 4 | Robô real, supervisionado | Autorização e fase 3 aprovada | Proposta |

### Requisitos das fases 2 a 4

- **Confirmação humana antes de qualquer movimento** (proposta). O nó mostra o destino entendido e espera a confirmação, com prazo; sem resposta, não faz nada. "Pare" não pede confirmação. A medição da fase 1 mostra que o modelo erra em frases capciosas.
- **Parar durante a navegação.** A função `navegar` de `workspace/patrulha_oficial/patrol_loop.py` bloqueia até o fim: o nó precisa acompanhar a meta sem bloquear a recepção, para o "pare" cancelar.
- Reaproveitar de `patrol_loop.py` os pontos, a espera por `map→odom` e a volta à doca. Sair da doca antes de navegar.
- Um controlador por vez: nunca junto de um programa de patrulha.
- Bateria real do `battery_state` na validação.

### Decisão em aberto: onde o modelo é consultado no simulador

O Ollama escuta só em `127.0.0.1`. Os contêineres do robô usam a rede do PC e o alcançam (testado). Os do simulador usam rede isolada (`infra/compose/sim.yaml`) e não alcançam. Opções: interpretar no PC e entregar ao contêiner só a ação já validada; ou configurar o Ollama para escutar também na ponte do Docker. A primeira não altera o serviço do PC.

### Sobre o simulador

O Gazebo não tem um mundo igual ao `mapa_lab_novo`. O simulador leve (`lab.sh sim subir leve`) aceita um mapa pela variável `MAPA`; com o `mapa_lab_novo` isso ainda não foi testado. Ele usa base, doca e bateria falsas.

## Aprovação humana

O manual e o `natural_language_nav.py` **não preveem aprovação de cada ação**. A única trava é o parâmetro `parking_brake` (ligado por padrão): ligado, nada é executado; desligado, o código escrito pelo modelo é executado na hora com `exec()`. Em caso de erro, o nó só registra a falha. A aprovação por ação e a validação são acréscimos nossos.

## Medição da fase 1 (25/11, CPU do PC do laboratório)

Com os destinos de `workspace/llm/destinos.json` em frases ("perto da janela e da mesa central"):

| Conjunto de frases | Acertos | Moveria errado | Outros erros | Observação |
|---|---|---|---|---|
| `ajuste.json` | 18/18 | 0 | 0 | Usado para ajustar (a regra de dois destinos nasceu aqui) |
| `reserva.json` | 13/14 | 0 | 1 ("desligue o robô" virou parar) | Escrito antes do ajuste |
| `estresse.json` | 12/16 | **4** | 0 | Frases capciosas; sem ajuste |
| `locais.json` | 19/21 | **2** | 0 | Nomes dos locais; usado para escolher o formato das descrições |

Mediana de 0,55 s por pedido, com o modelo já carregado. Erros que moveriam: "saia do ponto 2", "talvez amanhã você vá ao ponto 2", "diga ponto 2", "vá à geladeirinha e volte para a doca", "vá até a cadeira" e "vá da janela para a porta". "Vai pra janela", "vai pra porta" e "vai pro microondas" foram entendidas.

**Formato das descrições:** foi comparado com uma lista de nomes curtos ("janela; mesa central"), que se saiu pior: 3 erros que moveriam em `locais.json` (contra 2), 1 em `reserva.json` (contra 0) e 1 recusa indevida em `ajuste.json`.

Em `estresse.json`, "vá até a porta" passou de recusa a destino válido quando a porta virou um local. As amostras são pequenas e escritas por uma só fonte; não representam o uso real.

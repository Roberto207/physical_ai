# Plano: integração com LLM no TurtleBot 4

**Data:** 2026-11-25. **Estado:** execução escrita e ensaiada com robô falso; falta simulador e robô.

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
| Parâmetros `model_name` e `parking_brake` (ligado por padrão) | Feito; com o freio ligado nada é enviado ao robô |
| Ocupado, o nó ignora novos pedidos | Vale enquanto interpreta, exceto "parar". Durante o trajeto muda (ver desvios) |
| Coordenadas livres com direção, `dock` e `undock` | Feito na interpretação (decisão do operador) |
| `TurtleBot4Navigator` para navegar, encaixar e sair da doca | Feito, pelos clientes de ação (ver desvios) |

## Desvios

| Desvio | Motivo | Decisão |
|---|---|---|
| Ollama local no lugar da API da OpenAI | Gratuito | Aceito pelo operador |
| "Parar" atendido mesmo com o nó ocupado | Poder interromper | Aceito pelo operador |
| JSON por esquema e validador no lugar de `exec()` | O modelo erra e o código rodaria direto | Em uso; confirmar antes da execução |
| Sem dock e pose `[0, 0]` automáticos na partida | Usamos 2D Pose Estimate; a doca não está em `[0, 0]` | A confirmar antes da execução |
| Mensagem durante o trajeto cancela a meta e vira a ordem principal | Poder interromper e corrigir | Aceito pelo operador; feito |
| Durante dock e saída, a manobra termina e a última mensagem é obedecida; só "parar" cancela | Não deixar o robô meio encaixado | Aceito pelo operador; feito |
| Do navegador usam-se `getPoseStamped` e os clientes de ação; não `startToPose`, `goToPose`, `cancelTask`, `dock`, `undock` | Os atalhos esperam sem prazo e, numa recusa, guardam o resultado anterior | Aceito pelo operador; feito |
| No robô, o nó roda direto, sem `ros2 launch` | O launch morria no `docker stop` antes de o nó cancelar | Em uso (achado no ensaio) |
| Dock e saída da doca por software no robô real | A execução pedida inclui `dock` e `undock`; antes, o `lab.sh` mandava fazer à mão (SEG-06) | Aceito com o plano de execução |
| Locais por nome (`destinos.json`), voltar à doca e parar | Nosso mapa e segurança | Em uso |
| Coordenada conferida no mapa; bateria mínima de 20% para sair | Não mandar o robô para onde o mapa não permite | Em uso |
| Coordenadas e `dock`/`undock` lidos por código | O modelo inventou números e trocou `undock` por `dock` nos ensaios | Em uso |
| Nó `llm_node`, pacote `llm_tb4`, parâmetros `ollama_url`, `mapa` e `bateria_simulada`, namespace `/robot1` | Configuração do projeto | Em uso |

## Fases

| Fase | Entrega | Critério para avançar | Estado |
|---|---|---|---|
| 1 | Interpretador, testes e medição | Testes sem modelo passam; erros medidos | **Feita** |
| 2 | Plano alinhado ao tutorial | Desvios listados | **Feita** |
| 3 | Pacote e nó sem movimento, isolado | `test/ensaio_no.py` sem falhas | **Feita** |
| 4 | Código de execução, com robô falso | `test/ensaio_execucao.py` sem falhas | **Feita** |
| 5 | Execução no simulador | Ir, parar e voltar à doca observados | Pendente; o simulador é do operador |
| 6 | Robô real, supervisionado | Autorização; primeiro com o freio ligado | Pendente |

## Como a execução se comporta

| Pedido | Passos |
|---|---|
| Ir a local ou coordenada | Sair da doca, se encaixado; navegar. Local nomeado olha o ponto seguinte; coordenada sem direção usa 0° |
| Voltar à doca | Navegar ao ponto 1 virado para a doca; encaixar |
| Encaixar | Só fora da doca e com a doca visível |
| Sair da doca | Só se encaixado |
| Parar | Cancela a meta nossa e qualquer outra de navegação; apaga ordem pendente |

| Estado | Mensagem nova |
|---|---|
| Parado, interpretando | Ignorada, menos "parar" |
| Navegando | Cancela na chegada; a nova vira a ordem; se não for válida, o robô fica parado |
| Dock ou saída | A manobra termina; a última mensagem é obedecida. "Parar" cancela |
| Cancelando | Guarda a última; nada é enviado antes de o servidor confirmar o fim |
| Travado (sem confirmação) | Movimento recusado; "parar" repete o cancelamento |

**Antes de cada passo:** doca conhecida, bateria recente (≥ 20% para sair), `map→odom` recente, servidor de ação pronto e nenhuma meta de outro programa. No trajeto, perda de localização ou do estado da doca cancela; bateria baixa só avisa. **Prazos:** aceite 10 s, navegação 120 s, dock e saída 60 s, confirmação da doca 20 s, cancelamento 5 s, interpretação válida por 10 s. Coordenada a menos de 0,5 m da doca é recusada.

**Limites:** se o processo morrer à força, o Nav2 segue até o destino; fechar o terminal `falar` não para o robô; `lab.sh robo parar` não é parada de emergência; o texto não substitui a parada física.

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

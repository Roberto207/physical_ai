# O projeto: briefing, escopo e missões

## 1. Briefing original (mensagem do coordenador)

Projeto AKCIT sobre Physical AI com gêmeos digitais (INF-UFG).

- Problemas com diferentes tipos de robôs e plataformas (humanoides, quadrúpedes, com rodas etc.).
- Objetivo: combinar sensores, gêmeos digitais e atuação no mundo físico, com agentes capazes de agir, planejar e interagir.
- Objetivo secundário: formar mais pessoas em robótica e Physical AI.

Definido na primeira reunião:

- Nossa equipe (pouca base em robótica) estuda: ROS, Docker, Linux e, principalmente, a documentação do TurtleBot.
- TurtleBot é o robô de aprendizado inicial.

## 2. Escopo

- Duração: cerca de 10 meses (a confirmar com o coordenador).
- Produto final: ainda indefinido.
- Robôs previstos: humanoides, quadrúpedes, com rodas etc. Os TurtleBots são o aprendizado inicial.
- Gêmeo digital do INF já existe. A plataforma não foi confirmada, mas o Gazebo foi citado.
- Os robôs estão fisicamente no INF.

Dois níveis de objetivo na equipe:

| Nível | Quem | Objetivo |
|---|---|---|
| Iniciante | quem está começando | Entender como o robô funciona (hardware, software, IA) e saber operá-lo |
| Avançado | parte mais experiente da equipe, e nós depois | Pesquisar e aplicar o que funciona e o que não funciona em cada área de Physical AI, com possibilidade de publicar |

## 3. Missões designadas à nossa equipe (primeira task)

Prazo: cerca de 1 mês e meio a partir de 2026-11-05, conforme o Roberto. Data exata a confirmar com o coordenador.

### 3.1 Patrol control: patrulha do TurtleBot

- Existe um exemplo oficial chamado `patrol_loop` no pacote `turtlebot4_python_tutorials`. O robô dirige em loop e monitora a bateria. Quando a carga fica baixa, volta à base para carregar.
- É construído sobre o **TurtleBot 4 Navigator**: um nó Python que estende o Nav2 Simple Commander e acrescenta docking e undocking.
- O `TurtleBot4Navigator` vem do pacote `turtlebot4_navigation`, instalado nas imagens. Os tutoriais do GitHub (ramo `humble`) só são compilados no alvo `llm` do `infra/docker/Dockerfile`, que não é usado. Segundo o manual, os exemplos foram pensados para rodar em simulação.
- Em uso no robô: os programas adaptados do exemplo oficial, em `workspace/patrulha_oficial/` (volta à doca ou loop contínuo).
- Antes deles, a equipe escreveu o pacote `patrulha_tb4`, com recarga automática, descrito em `specs/patrol-inf/`.

### 3.2 Integração de uma LLM ao TurtleBot

- Existe o pacote oficial `turtlebot4_openai_tutorials`, com o módulo `natural_language_nav`. Ele usa a API antiga da OpenAI e executa com `exec()` o que o modelo escreve, então serve de referência, não de base.
- A nossa abordagem: a LLM escolhe entre ações discretas validadas (`workspace/meu_ws/src/llm_tb4/llm_tb4/validar_acao.py`) e nada é executado com `exec`.
- LLM escolhida (25/11): **Ollama** com `qwen2.5:1.5b`, gratuito e local.

### 3.3 Links de foco (passados no grupo)

- https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html
- https://turtlebot.github.io/turtlebot4-user-manual/

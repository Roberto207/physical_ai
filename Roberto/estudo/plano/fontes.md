# Fontes, com links

## Como escolhi

Primeiro a documentação oficial, depois o que o grupo indicou, depois os materiais que a busca trouxe. **Não medi popularidade:** "recomendado" aqui significa oficial ou indicado pelo grupo.

Legenda de verificação:

- **Li:** o conteúdo da página foi lido nesta pesquisa.
- **Título:** só li o título. Vídeo nenhum foi assistido.
- **Abre:** só confirmei que o endereço responde. `docs.ros.org` bloqueia leitura automática, então a resposta pode ser só a tela de bloqueio. Se um link falhar, comece pelo índice da seção.

## Passados pelo grupo

| Fonte | Para quê | Verificação |
|---|---|---|
| [Manual do TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/) | Referência principal do robô | Li |
| [TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) | A API das duas missões. Tem as seções Patrol Loop e LLM | Li |

## Do relatório do Gabriel

| Fonte | Para quê | Verificação |
|---|---|---|
| [What is ROS? Why are robots built using ROS?](https://www.youtube.com/watch?v=979IZWOXC_0) | Primeira ideia do que é ROS | Título |
| [Get familiar with the TurtleBot 4 in 5 minutes](https://www.youtube.com/watch?v=tlXa2TTpQrw) | Hardware do robô | Título |
| [How to Set Up Your TurtleBot 4 with ROS 2 Jazzy](https://www.youtube.com/watch?v=TPXzNKgafJg) | Setup do robô real | Título |
| [Canal Articulated Robotics](https://www.youtube.com/@ArticulatedRobotics) | Simulação e ROS. O Gabriel indica o canal inteiro | Abre |
| [Clearpath Robotics](https://clearpathrobotics.com/) | Fabricante do TurtleBot 4 | Não verifiquei |
| [Basic Setup](https://turtlebot.github.io/turtlebot4-user-manual/setup/basic.html) e [Simple Discovery](https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html) | Ligar o robô real à rede | Só o índice do manual |

## ROS 2 (semanas 1 e 2)

| Fonte | Para quê | Verificação |
|---|---|---|
| [Tutoriais: ferramentas de linha de comando](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html) | Semana 1, é o principal | Abre |
| [Entendendo actions](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html) | A peça mais importante para as missões | Abre |
| [Conceito de actions](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Actions.html) | Explicação curta do conceito | Abre |
| [Tutoriais: bibliotecas cliente](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries.html) | Semana 2, índice | Abre; a busca confirma o conteúdo |
| [Publisher e subscriber em Python](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html) | Semana 2 | Abre |
| [Action server e client em Python](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Py.html) | Semana 2 | Abre |
| [Robotics Back-End](https://roboticsbackend.com/category/ros2/) e [canal](https://www.youtube.com/@RoboticsBackEnd) | Explicação alternativa, se a oficial não entrar | Abre |
| [Tutorial do Murilo Marinho](https://ros2-tutorial.readthedocs.io/) | Curso linear gratuito para Jazzy e Ubuntu 24.04 | Só o trecho da busca |
| [Automatic Addison](https://automaticaddison.com/tutorials/) | Índice grande, com Jazzy e Nav2. Bom para consulta | Abre |

## Nav2 e TurtleBot 4 (semana 3)

| Fonte | Para quê | Verificação |
|---|---|---|
| [Hardware do TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/overview/features.html) | Tabela de peças | Li |
| [Navegação no TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html) | Comandos e pose inicial | Li |
| [Criar mapa](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/generate_map.html) | Obrigatório no robô real | Li |
| [Simulador do TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_simulator.html) | Argumentos e mundos | Li |
| [Simulação: requisitos](https://turtlebot.github.io/turtlebot4-user-manual/software/simulation.html) | O manual recomenda PC com GPU dedicada | Li |
| [Create 3](https://turtlebot.github.io/turtlebot4-user-manual/software/create3.html) | Actions da base, como Dock e Undock | Li |
| [Primeiros passos do Nav2](https://docs.nav2.org/rolling/getting_started/) | Visão geral | Abre. É a versão `rolling`, não Jazzy |
| [Simple Commander API](https://docs.nav2.org/rolling/configuration_and_development/simple_commander_api/simple_commander_api/) | `goToPose`, `isTaskComplete`, `cancelTask` | Abre. É a versão `rolling` |
| [Simulador leve, README para Jazzy](https://api.nav2.org/nav2-jazzy/html/md_nav2_loopback_sim_README.html) | O que ele simula e o que não simula | Li |

## Código (semanas 3 a 5)

| Fonte | Para quê | Verificação |
|---|---|---|
| [turtlebot4_tutorials, branch jazzy](https://github.com/turtlebot/turtlebot4_tutorials/tree/jazzy) | Todos os exemplos. **Já está na imagem:** `/opt/tb4_ws/src/turtlebot4_tutorials` | Compilei |
| [patrol_loop.py](https://raw.githubusercontent.com/turtlebot/turtlebot4_tutorials/jazzy/turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py) | Base da missão 1 | Li e rodei |
| [natural_language_nav.py](https://raw.githubusercontent.com/turtlebot/turtlebot4_tutorials/jazzy/turtlebot4_openai_tutorials/turtlebot4_openai_tutorials/natural_language_nav.py) | Referência da missão 2, não é para copiar | Li; não rodei |

**Atenção:** o manual e o PDF mandam instalar com `sudo apt install ros-$ROS_DISTRO-turtlebot4-tutorials`. Em 5/nov/2026 esse pacote não existe no repositório do Jazzy, por isso compilei do GitHub.

## LLM (semana 5)

| Fonte | Para quê | Verificação |
|---|---|---|
| [Gemini: function calling](https://ai.google.dev/gemini-api/docs/function-calling) e [limites](https://ai.google.dev/gemini-api/docs/rate-limits) | Opção com plano gratuito | Abre |
| [Groq: limites](https://console.groq.com/docs/rate-limits) | Opção com plano gratuito | Abre |
| [Comparativo de APIs gratuitas (OpenRouter)](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/) | Visão geral | Só o trecho da busca. As fontes divergem nos números, confira na página do provedor |
| [ROSA, da NASA JPL](https://github.com/nasa-jpl/rosa) | Agente LLM para ROS, feito sobre LangChain. Leitura, não para este prazo | Abre. Licença a conferir |
| [Artigo: várias LLMs com Nav2 (Sensors, 2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12846292) | Para comparar com a sua avaliação | Só o trecho da busca |

## Ambientes remotos

| Fonte | Para quê | Verificação |
|---|---|---|
| [FAQ do Colab](https://research.google.com/colaboratory/faq.html) | Regras e limites | Li |
| [Documentação de notebooks do Kaggle](https://www.kaggle.com/docs/notebooks) | Regras e limites | A página veio vazia para mim. **Leia você** |
| [The Construct](https://www.theconstruct.ai/) | ROS pelo navegador | Abre. Limites atuais desconhecidos |

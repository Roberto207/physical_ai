# Missões iniciais: patrol control e LLM no TurtleBot

Fonte: PDF do colega Gabriel Santiago Vidal (`../../Relatório de estudos TurtleBot .pdf`) e links do grupo.
Os itens marcados como "a confirmar" ainda não foram verificados por nós.

## 1. Patrol control

- Existe um exemplo oficial chamado `patrol_loop` no pacote `turtlebot4_python_tutorials`.
- O robô dirige em loop e monitora a bateria. Quando a carga fica baixa, volta à base para carregar.
- É construído sobre o **TurtleBot 4 Navigator**: um nó Python que estende o Nav2 Simple Commander e acrescenta docking e undocking.
- Instalação: o PDF e o manual citam `sudo apt install ros-$ROS_DISTRO-turtlebot4-tutorials`, mas esse pacote não existe para Jazzy (verificado em 2026-11-05). Compilado do GitHub, já na imagem `physical-ai:jazzy`.
- Segundo o manual, os exemplos foram pensados para rodar em simulação.

## 2. Integração com LLM

- Existe o pacote oficial `turtlebot4_openai_tutorials`, com o módulo `natural_language_nav`.
- O branch `jazzy` existe e compila, mas não há pacote apt. O código usa a API antiga da OpenAI e executa com `exec()` o que o modelo escreve, então serve de referência, não de base. Ver `../../estudo/semana-5-missao-llm.md`.
- Provedor de LLM em aberto: a sugestão é começar com API de plano gratuito.

## Prazo

Cerca de 1 mês e meio a partir de 2026-11-05, conforme o Roberto. Data exata a confirmar. Plano em `../../estudo/README.md`.

## Links de foco (passados no grupo)

- https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html
- https://turtlebot.github.io/turtlebot4-user-manual/

# Semana 1: ROS 2 na mão, sem escrever código (8 horas)

## O que é esta semana

Você vai aprender as quatro formas pelas quais os programas de um robô conversam, usando uma tartaruga 2D na tela (`turtlesim`). Ela é um robô de brinquedo: recebe velocidade, informa a posição e aceita tarefas, igual ao TurtleBot.

## Por que começar aqui

Mesmo sem saber Python de ROS, com o terminal você já consegue perguntar a qualquer robô "quem está rodando, o que publica, o que aceita". É a ferramenta que você vai usar em toda depuração até o fim do projeto. E os comandos são os mesmos no TurtleBot real.

## O que é ROS, em 1 minuto

ROS significa *Robot Operating System*, mas não é sistema operacional: é um conjunto de bibliotecas e ferramentas que roda sobre o Linux. Em vez de um programão, o robô é feito de vários programas pequenos, os **nós**, que trocam mensagens.

Numa cozinha de restaurante:

| Conceito | Quando usar | Na cozinha | No TurtleBot |
|---|---|---|---|
| **Topic** | Fluxo contínuo, sem esperar resposta | O quadro de pedidos: um escreve, vários leem | `/scan` (lidar), `/battery_state` |
| **Service** | Pergunta rápida com resposta | "Tem salmão hoje?" | Consultar um estado |
| **Action** | Tarefa demorada, com progresso e como cancelar | "Faça 40 pratos" e te avisam a cada 10, e dá para cancelar | `/navigate_to_pose`, `/dock` |
| **Parameter** | Ajuste de configuração | A temperatura do forno | Velocidade máxima |

**Se só uma coisa ficar desta semana, que seja action.** Mandar o robô até um lugar demora, pode falhar e pode precisar ser cancelado. Por isso a navegação é uma action, e as suas duas missões giram em torno dela.

## O que estudar (cerca de 3 horas)

| Ordem | Material | O que tirar dele | Tempo |
|---|---|---|---|
| 1 | [What is ROS?](https://www.youtube.com/watch?v=979IZWOXC_0) | A ideia geral | não sei a duração |
| 2 | [TurtleBot 4 em 5 minutos](https://www.youtube.com/watch?v=tlXa2TTpQrw) | Como é o robô | 5 min |
| 3 | [Hardware no manual](https://turtlebot.github.io/turtlebot4-user-manual/overview/features.html) | A tabela abaixo | 15 min |
| 4 | [Tutoriais de linha de comando](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html): nodes, topics, services, parameters, actions | Fazer junto, não só ler. **Pule a parte de instalação:** seu ambiente está pronto | 2 h |
| 5 | [Conceito de actions](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Actions.html) | Goal, feedback, result | 15 min |

As peças do robô, conforme o manual:

| Peça | Função | TurtleBot 4 | TurtleBot 4 Lite |
|---|---|---|---|
| iRobot Create 3 | A base: rodas, sensores de contato, base de carga | sim | sim |
| Raspberry Pi 4B 4 GB | O computador | sim | sim |
| RPLIDAR A1M8 | Lidar: mede a distância em volta | sim | sim |
| Câmera | Imagem e profundidade | OAK-D-Pro | OAK-D-Lite |
| Bateria | 26 Wh, de 2h30 a 4h de uso | sim | sim |

## Praticar (cerca de 4 horas)

Da raiz do projeto, abra dois terminais, cada um com `infra/docker/ros.sh`.

No terminal 1, a tartaruga (uma janela vai abrir):

```bash
ros2 run turtlesim turtlesim_node
```

No terminal 2, investigue:

```bash
ros2 node list                                  # quem está rodando?
ros2 node info /turtlesim                       # o que esse nó publica, assina e aceita?
ros2 topic list
ros2 topic echo /turtle1/pose                   # lê a posição. Ctrl+C para sair
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 2.0}}'   # anda
ros2 interface show geometry_msgs/msg/Twist     # qual é o formato dessa mensagem?
ros2 action list
ros2 action send_goal /turtle1/rotate_absolute turtlesim/action/RotateAbsolute '{theta: 1.57}' --feedback
```

Testei a publicação de velocidade, a leitura da pose e a action. Veja o feedback da última linha: é o mesmo mecanismo do "faltam 40 s para chegar" da navegação.

Exercícios, sem olhar a resposta:

1. Faça a tartaruga andar em círculo com um único comando. Dica: `-r 1` repete e o campo `angular.z` faz girar.
2. Descubra, só pelo terminal, qual service cria uma segunda tartaruga, e crie.
3. Mande uma rotação grande e, enquanto ela gira, mande outra action. O que acontece com a primeira?

No fim: `infra/docker/ros.sh parar`.

## Fora do computador (1 hora)

- Pergunte ao coordenador: "pronto" é em simulação ou no robô real? Como acesso o servidor do INF? Qual modelo de robô?
- Veja o robô de perto se puder, e identifique cada peça da tabela.

## Pronto quando

Você explica a um colega, em 2 minutos e com exemplo, a diferença entre topic, service e action, e faz os 3 exercícios.

## Se travar

- Janela não abre: confira `echo $DISPLAY` no seu terminal fora do container, e tente `infra/docker/ros.sh parar` e abrir de novo.
- `ros2 action list` vazio: a tartaruga não está rodando no outro terminal.
- O tutorial pede `apt install`: o que precisar já está na imagem. Se não estiver, me avise.

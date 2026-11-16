# Conceitos: o que é cada coisa

## Resposta direta

O projeto é um robô que patrulha sozinho (TurtleBot 4), e ainda não temos o robô. Por isso usamos **simuladores**: programas que fingem o robô e o ambiente, em graus diferentes de realismo. Quanto mais realista, mais pesado para o computador.

## A cena do dia a dia

Pense em ensinar alguém a dirigir:

| Etapa | Na autoescola | No projeto |
|---|---|---|
| Regras no papel | Aula de legislação | Testes em Python puro (`pytest`) |
| Jogo simples | Simulador de tela | `turtlesim` |
| Simulador de rota | GPS com carro de brinquedo | Simulador leve com Nav2 |
| Simulador realista | Cabine de simulador com física | Gazebo |
| Carro de verdade | Rua | Robô real no INF |

## TurtleBot 4

O "4" é a **geração** do robô. A linha TurtleBot é educacional, e cada número é uma versão mais nova. O TurtleBot 4 foi feito pela Clearpath com a iRobot (a base é a do Roomba), tem lidar, câmera e roda ROS 2. Os anos de lançamento de cada geração não foram verificados por nós.

Há duas versões, **Standard** e **Lite**, com menos sensores na Lite. Qual delas o INF tem é uma pergunta em aberto.

## Docker: imagem, camadas e container

A imagem `physical-ai:jazzy` é um **prédio de andares empilhados**, não imagens uma dentro da outra:

| Andar | Conteúdo | Quem pôs |
|---|---|---|
| Térreo | Ubuntu 24.04 | Imagem base `ros:jazzy-ros-base` |
| 1º | ROS 2 Jazzy | A mesma imagem base |
| 2º | Simulador do TurtleBot 4, Nav2, Gazebo, turtlesim | Nós, no `Dockerfile` |
| Cobertura | Tutoriais `patrol_loop` e `openai`, compilados do GitHub | Nós |

- **Imagem** é a receita congelada. **Container** é a imagem rodando. Quando o container é removido, tudo dentro dele some, menos o que está na pasta `workspace/`.
- O robô **não está na imagem**. Lá dentro roda só um modelo de software dele. O robô físico está no INF.
- **Por que Docker:** o notebook roda Debian, e o ROS 2 Jazzy só é suportado no Ubuntu 24.04. O container traz o Ubuntu junto, sem mexer no sistema da máquina.
- **Por que limite de memória:** um `docker build` sem teto travou o notebook em 5/nov. Desde então, tudo roda com `--memory`.

## ROS 2

O "rádio" pelo qual os programas do robô conversam. Peças que aparecem nos testes:

| Peça | O que é | Exemplo |
|---|---|---|
| Node | Um programa | O que desenha a tartaruga; o `patrol_loop` |
| Topic | Canal de mensagens contínuas | `/cmd_vel` (velocidade), `/odom`, `/battery_state` |
| Service | Pedido pontual com resposta | Mudar a cor do rastro da tartaruga |
| Action | Pedido longo com acompanhamento | "Vá até o ponto X" (`navigate_to_pose`), `/dock`, `/undock` |

## turtlesim

A "autoescola do ROS": uma tartaruga 2D numa janela. Sem robô, sensor ou física, então é leve e serve para treinar nodes, topics, services e actions. Aprender action ali prepara para entender como o Nav2 recebe um destino.

## Gazebo

Um "videogame de física para robôs". Simula rodas, colisões, lidar e câmera, e o programa do robô acha que fala com sensores reais. Serve para errar sem quebrar nada. O custo é computacional: o seu notebook roda o Gazebo bem abaixo do tempo real.

**RTF** (Real Time Factor) é a velocidade da simulação em relação ao relógio. RTF de 0,18 significa que 10 s de simulação levam cerca de 55 s reais.

## Nav2

O "GPS com piloto automático" do robô. Você dá um destino e ele calcula a rota e dirige, desviando de obstáculos.

| Etapa | Pergunta | Viagem de carro |
|---|---|---|
| Mapa | Como é o lugar? | Mapa da cidade |
| Localização (AMCL) | Onde estou? | Ponto azul do GPS |
| Planejador global | Por onde vou? | GPS traçando a rota |
| Controlador local | Como sigo agora? | Você no volante, desviando |
| Recuperação | E se travar? | Dar ré e tentar outro caminho |

É pacote pronto. Nossa missão é usar o Nav2, não reescrevê-lo.

## Simulador leve (`nav2_loopback_sim`)

A versão "de mentira" do Gazebo. Sem física e sem sensores desenhados: ele pega a velocidade comandada e calcula onde o robô estaria. O Nav2 é o real.

| | Gazebo | Simulador leve |
|---|---|---|
| Física e sensores | Sim | Não |
| RAM | cerca de 1,9 a 2,6 GiB | cerca de 0,5 a 0,7 GiB |
| Serve para | Ver o robô "viver" | Exercitar a lógica e a API do Nav2 |
| Base de carga e bateria | Reais na simulação | **Falsas**, escritas por nós (`infra/tools/fake_tb4_base.py`) |

Atenção ao que ele não prova: nada sobre o robô real, como docking, obstáculos inesperados ou duração da bateria. Também não vale usar o `/amcl_pose` dele para saber onde o robô está, porque é uma resposta fixa da nossa base falsa. Use o `tf` (`map` para `base_link`).

## Lidar e câmera

- **Lidar:** sensor que mede distâncias com laser, girando em volta do robô. No Gazebo entregou 640 raios por volta, de -180° a 180°, alcance de 0,16 a 12 m.
- **Câmera (OAK-D):** no Gazebo entrega imagem de 320 x 240.
- **Bateria e dock:** `/battery_state` e `/dock_status` dizem a carga e se o robô está na base. A patrulha depende dos dois.

## Efeito prático

Quando alguém perguntar "o que você testou", a resposta honesta tem duas partes: o **realismo** (Gazebo) e a **lógica** (simulador leve). A patrulha foi validada na lógica, e o realismo ainda depende de servidor melhor e do robô.

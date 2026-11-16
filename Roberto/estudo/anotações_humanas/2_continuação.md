# ============================================================================
## 1. URDF Files: 

**Unified Robot Description Format (URDF)** é um arquivo XML que descreve a estrutura do robô. **Ficha técnica que os progamas consultam para saber as especificações do robô**, como tamanho, forma, massa, inércia, limites de movimento e sensores. O **URDF é usado para simulação, visualização e controle do robô.**

- Links: Partes rígidas do robô, como braços, rodas e sensores. Cada link tem uma geometria, massa e inércia associadas.

- joint: Encaixe entre duas peças do robô, permitindo movimento relativo entre elas. Cada joint tem um tipo (revolute, prismatic, fixed, etc.) e limites de movimento.

- Visual: Representação visual do link, usada para renderização em simuladores e visualizadores.

- Collision: Caixa de colisão, no formato de cada link, usada para detecção de colisão.

- Inertial: Peso de cada peça.

- Origin: Posição e orientação do link ou joint.

# ===========================================================================
## 1.2 Xacro Files:

- URDFS normalmente ficam muito grandes e repetítivos (duas rodas iguais por exemplo, precisam ser descritas duas vezes). Para resolver isso, o ROS2 utiliza arquivos **Xacro**, que são arquivos XML com recursos de progamação, como variáveis, macros e loops. O Xacro permite gerar arquivos URDF de forma mais compacta e reutilizável. **O Xacro é processado pelo ROS2 para gerar o URDF final que será usado pelos nós do robô.**

- **No nosso projeto**: o URDF já vem pronto, e nós só o usamos. Pelo launch file do simulador leve (tb4_loopback_simulation.launch.py), ele carrega o modelo turtlebot4.urdf.xacro do pacote nav2_minimal_tb4_description e o entrega ao robot_state_publisher. Isso aparece no nosso sistema de três maneiras:

    1. O robo desenhado no RViz (uma ferramenta de visualização do ROS2, que mostra o robô e seus sensores em 3D).
    2. Erros e logs.
    3. Para o Nav2, que precisa saber o tamanho do robô para planejar caminhos e evitar obstáculos.
    4. Para o Gazebo, que precisa saber o tamanho do robô para simular a física e a colisão com o ambiente.


# ===========================================================================
## 2. RViz :

- Ferramenta de visualização do ROS2, que permite ver o robô, seus sensores e o ambiente em 3D. O RViz é usado para depuração, monitoramento e interação com o robô. Tela de monitoramento do robô. Ele desenha o que chega pelos tópicos: o mapa, o robô, a rota planejada, sensores, etc... 

- **O que o RViz não faz:** simular física (isso é o Gazebo), criar mapa (isso é o SLAM) ou calcular rotas (isso é o Nav2).

- **O RVzi sobre junto de outras ferramentas,** como o Gazebo (simulador de robótica), o Nav2 (pacote de navegação) e o SLAM (pacote de mapeamento) e recebe dados de todos eles (através de **tópicos**) para mostrar o estado do robô e do ambiente. Ele é uma ferramenta de visualização, não de controle ou planejamento.

- **RViz é a sua melhor ferramenta de investigação:** quando a navegação falhar de novo, é nele que você vê se o robô está preso por um costmap, se a rota existe, ou se a localização está errada. E para o gate de entrega, é a melhor forma de demonstrar a patrulha funcionando.

- **Exemplo na simulação gazebo:**

    Um galpão com segurança e sala de controle:
    ┌────────────────────────────────────────────────────────────┬─────────────────┐
    │                          Na cena                           │   No projeto    │
    ├────────────────────────────────────────────────────────────┼─────────────────┤
    │ O galpão de verdade, com paredes e objetos                 │ O mundo do      │
    │                                                            │ Gazebo          │
    ├────────────────────────────────────────────────────────────┼─────────────────┤
    │ O monitor da sala de controle, que mostra o que os         │ O RViz          │
    │ sensores informam                                          │                 │
    ├────────────────────────────────────────────────────────────┼─────────────────┤
    │ O cabo que leva os sinais dos sensores até o monitor       │ Os tópicos do   │
    │                                                            │ ROS             │
    └────────────────────────────────────────────────────────────┴─────────────────┘

- Caso 1: com o Gazebo

    Gazebo (mundo 3D e física)
    |  ponte (ros_gz_bridge) converte as mensagens do Gazebo para o ROS
    v
    /scan, /odom, /tf, /clock, imagens da câmera ...
    |
    v
    RViz (mostra o que o robô "sente")

- O Gazebo calcula a física e gera os sensores. A ponte leva os dados dele para o ROS. No launch que lemos, vimos a ponte do relógio (/clock). Não li as outras pontes, mas os tópicos /scan, /odom e /oakd/... apareceram no ROS, então os dados chegam.
- O Gazebo tem a janela dele, que mostra o mundo como ele é. O RViz é outra janela, que mostra o que o robô sabe. São dois programas separados.

Caso 2: com o simulador leve

    Nav2 -- /cmd_vel --> loopback_simulator (calcula a posição)
                            |
    map_server --> /map   |  tf (posição do robô)
    robot_state_publisher --s peças
    fake_tb4_base --> /battery_state, /dock_status      (nosso, falso)
                            |
                            v
                        RViz

Aqui não existe janela de mundo, o Rviz é a única forma  de ver alguma coisa

# ===========================================================================
## 3. SLAM :

-  **SLAM (Simultaneous Localization and Mapping, ou localização e mapeamento simultâneos) é a técnica em que o robô desenha o mapa de um lugar desconhecido enquanto descobre onde está nele.** Não é um simulador como o Gazebo, e sim um algoritmo que roda junto com o robô, real ou simulado.

- Como funciona no turtlebot4: 

    ┌───────────────────────────┬─────────────────────────────────────────────────────────────────┐
    │           Peça            │                              Papel                              │
    ├───────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ Lidar (/scan)             │ Mede a distância até as paredes ao redor                        │
    ├───────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ Odometria (/odom)         │ Estimativa de quanto as rodas andaram                           │
    ├───────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ SLAM Toolbox              │ O pacote que junta os dois e desenha o mapa                     │
    ├───────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ Mapa salvo (.yaml + .pgm) │ O resultado: uma imagem 2D vista de cima, como o warehouse.yaml │
    └───────────────────────────┴─────────────────────────────────────────────────────────────────┘

    - Você dirige o robô pelo lugar (com o teleop, por exemplo) e o mapa vai sendo construído. No fim, salva o mapa.

# ===========================================================================
## 3.1 AMCL:

- **AMCL (Adaptive Monte Carlo Localization) é o algoritmo que permite ao robô descobrir onde ele está em um mapa conhecido.** Ele usa a odometria e os sensores para comparar o que o robô vê com o que o mapa diz que deveria ver, e assim estima a posição do robô no mapa. Em mapas já fornecidos, se anda com AMCL e Nav2.

┌─────────────────┬────────────────────────────────────┬───────────────────────────────────────────────┐
│                 │                SLAM                │                     AMCL                      │
├─────────────────┼────────────────────────────────────┼───────────────────────────────────────────────┤
│ Tem mapa antes? │ Não, ele cria o mapa               │ Sim, ele usa um mapa pronto                   │
├─────────────────┼────────────────────────────────────┼───────────────────────────────────────────────┤
│ Quando usar     │ Primeira vez num lugar             │ Toda vez que for navegar num lugar já mapeado │
├─────────────────┼────────────────────────────────────┼───────────────────────────────────────────────┤
│ No nosso fluxo  │ Uma vez, para mapear o laboratório │ Durante a patrulha                            │
└─────────────────┴────────────────────────────────────┴───────────────────────────────────────────────┘

- Nas simulações leves nossas, o AMCL é falso: ele só diz "localização ativa" para o Nav2 aceitar iniciar. A posição verdadeira vem do "simulador leve" (loopback_simulator) que utiliza o comando /cmd_vel do Nav2 para calcular onde o robô estaria a partir da velocidade e da posição incial. O AMCL real, no robô, usaria os sensores de verdade (lidar e câmera) para estimar a posição.
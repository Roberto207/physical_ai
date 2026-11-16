# ====================================================================================================
## 1. Início: 

- O **ROS2 (Robotic operationg system)** é um **framework** (não um sistema operacional como a sigla diz) de software para robótica, que permite a comunicação entre diferentes partes de um sistema robótico, como sensores, atuadores e algoritmos de controle. Ele roda em **ubuntu** e é amplamente utilizado na indústria e na pesquisa em robótica.

- Na nossa máquina estamos utilizando uma **imagem docker para rodar o ROS2**, que já vem com todas as dependências necessárias para o desenvolvimento de aplicações robóticas. Estamos utilizando especificamente o ROS2 Jazzy. Na nossa imagem docker, estamos puxando algumas outras coisas, como o **Nav2**, que é um pacote de navegação para robôs móveis, o **Gazebo**, que é um simulador de robótica, e os pacotes **turtlesim** (uma tartaruga 2D para aprender os conceitos) e **TurtleBot 4** (o robô do projeto, com o simulador dele, que é o que traz o Gazebo). Esse conjunto é a imagem `physical-ai:jazzy`. Ela foi construída por cima da imagem base `ros:jazzy-ros-base`, que traz só o ROS 2 Jazzy sobre o Ubuntu 24.04.

## 1.2 Pacotes e executáveis
- **Pacotes são coleções** de código, bibliotecas e recursos que podem ser usados para construir aplicações robóticas. Cada pacote pode conter um ou mais        **executáveis, que são programas que podem ser executados no ROS2**. Por exemplo, o **pacote turtlesim** contém o **executável turtlesim_node**, que é o simulador do robô virtual, e o executável turtle_teleop_key, que permite controlar o robô usando o teclado. Ao executarmos o **turtlesim_node, ele cria um nó chamado /turtlesim.Todo nó em execução começa com /**.

    1. Nós utilizamos os seguintes pacotes, e alguns outros, visíveis no dockerfile: 
        - **turtlesim:** Pacote que contém o simulador do robô virtual e o teleop para controlar o robô.
        - **turtlebot4_gz_bringup:** Pacote que contém os arquivos de lançamento para iniciar o TurtleBot 4 no Gazebo.
        - **nav2_bringup:** Pacote que contém os arquivos de lançamento para iniciar o Nav2, que é o pacote de navegação para robôs móveis.
        - **ros_gz_sim:** Pacote que liga o Gazebo ao ROS 2 e contém o launch que inicia o simulador (usado pelo `sim_headless.launch.py`). No Jazzy ele substitui o antigo `gazebo_ros`, que não está na nossa imagem.

    2. Para rodar os executáveis, utilizamos o comando `ros2 run <nome_do_pacote> <nome_do_executavel>`. Por exemplo, para rodar o simulador do turtlesim, utilizamos o comando `ros2 run turtlesim turtlesim_node`. Ou para rodar o patrol_loop dentro de `treino_leve.sh`, utilizamos o comando `ros2 run turtlebot4_python_tutorials patrol_loop`



## 1.3 Nodes (Nós): 

- **ROS funciona se comunicando através de nós, que são processos que executam código. O nó é a instância de um executável em execução**
Nós funcionam tipicamente enviando ou recebendo dados, sendo possível ser feito de maneiras diferentes: **tópicos** (canais de comunicação contínuo dos nós), **serviços** (pedidos pontuais entre nós: uma pergunta e uma resposta rápida) e **ações** (tarefas que podem ser canceladas ou monitoradas. Pedidos demorados, com acompanhamento e possibilidade de cancelamento.). Cada nó pode **ter um ou mais tópicos, serviços e ações, dependendo da sua funcionalidade.**

Por exemplo, o executável (e nó quando em execução) `turtlesim_node` publica a posição do robô virtual no tópico `/turtle1/pose` e assina o tópico `/turtle1/cmd_vel`. O nó `turtle_teleop_key` publica os comandos de velocidade em `/turtle1/cmd_vel`, e é o `turtlesim_node` que os recebe e move a tartaruga na tela. Assinar um tópico significa que o nó está interessado em receber informações desse tópico (como um newsletter).

- Um nó nasce quando um executável é iniciado com o comando `ros2 run <nome_do_pacote> <nome_do_executavel>`. Por exemplo, o nó turtlesim_node é iniciado com o comando `ros2 run turtlesim turtlesim_node`, e o nó turtle_teleop_key é iniciado com o comando `ros2 run turtlesim turtle_teleop_key`.

- Dividir o robô em nós que se comunicam (sensores, atuadores e algoritmos de controle trabalhando juntos) é a ideia central do ROS, e já existia no ROS 1. O que o ROS 2 mudou foi a forma de comunicação: ela não depende mais de um nó central (o `roscore` do ROS 1) e passou a ter suporte a tempo real, configuração de qualidade da comunicação (QoS) e segurança. Por isso o ROS 1 foi sendo substituído.

- **Comandos com nós**: Todos os comandos sobre nós começam com ros2 node. Rode-os dentro do container `infra/docker/ros.sh`

    1. `ros2 node list` - lista todos os nós ativos no sistema.
    2. `ros2 node info <nome_do_no>` - mostra informações sobre um nó específico, como os tópicos que ele publica e assina, os serviços que ele oferece e as ações que ele suporta. Tudo de mais importante de um nó.
    3. `ros2 topic list` - lista todos os tópicos ativos no sistema (este é do grupo `ros2 topic`, e não do `ros2 node`).

    - O `ros2 node` só tem `list` e `info`. Para encerrar um nó, use `Ctrl+C` no terminal onde ele roda, ou pare o container. Para iniciar, rode o executável com `ros2 run`.

    - Para o turtlesim especicamente: (lembrando que `turtlesim_node` é o executável, `/turtlesim` é o nó e `turtlesim` é o pacote)
        1. `ros2 run turtlesim turtle_teleop_key` - inicia o nó que permite controlar o robô virtual usando o teclado.


- **Partes de um Nó**: 
    1. **Conjunto de comunicação entre nós:** Tópicos, serviços e ações. Exemplos: Topico /turtle1/pose (canal onde nós podem ver a posição da tartaruga), serviço /spawn (cria outra tartaruga), ação /turtle1/rotate_absolute (pedido longo, com progresso e pode ser cancelado). Algo muito interessante sobre as actions é que nós mesmos podemos criar nossas actions, definindo as metas (goals) que ele tem que executar até atingir. 
    2. **Código do nó:** O código que implementa a funcionalidade do nó, que pode ser escrito em C++ ou Python.
    3. **Parâmetros do nó:** Como os parâmetros de uma função. **Configurações que podem ser ajustadas para alterar o comportamento do nó, como a velocidade máxima do robô ou a frequência de atualização dos sensores. Parâmetros podem ser definidos em arquivos YAML e carregados no nó durante a inicialização.**



## 1.4 ROS Workspaces (Espaços de trabalho do ROS):

- Workspace é a pasta guarda-chuva onde é guardado o código do ROS2, incluindo pacotes, nós, arquivos de configuração e outros recursos, e onde **são compilados os pacotes e códigos do sistema** . **Ele é usado para organizar e gerenciar o desenvolvimento de aplicações robóticas, permitindo que diferentes partes do sistema sejam desenvolvidas e testadas separadamente, em diferentes pastas. Similarmente a um WORKDIR docker ou um folder de projeto. O ROS2 utiliza o conceito de workspaces para permitir que os desenvolvedores criem e gerenciem seus projetos de forma modular e escalável.**

- Para usar os pacotes de um workspace, é necessário **compilar o workspace** usando o comando `colcon build`, que compila todos os pacotes do workspace e gera os arquivos necessários para a execução dos nós. Após a compilação, é necessário **sourcar o workspace** usando o comando `source install/setup.bash`, que configura o ambiente do ROS2 para incluir os pacotes do workspace na busca de pacotes e executáveis.
    
    - criando um workspace e um pacote Python com um nó executável, podemos seguir os seguintes passos:
    
    ``` bash
    #1. criar o workspace e a pasta src
    mkdir -p meu_ws/src && cd meu_ws/src

    #2. criar um pacote Python com um executável
    ros2 pkg create --build-type ament_python --node-name meu_no meu_pacote

    #3. compilar (volte para a raiz do workspace)
    cd .. && colcon build --symlink-install
    Starting >>> meu_pacote
    Finished <<< meu_pacote [1.21s]

    #4. ligar o workspace a este terminal
    source install/setup.bash

    #5. rodar
    ros2 run meu_pacote meu_no
    # Hi from meu_pacote.
    ```

- **Estrutura de um workspace:** Um workspace do ROS2 geralmente contém as seguintes pastas:

    1. **src:** Pasta onde são armazenados os pacotes do ROS2, incluindo código-fonte, arquivos de configuração e outros recursos.
    2. **install:** Pasta onde são armazenados os arquivos instalados dos pacotes do seu workspace, incluindo bibliotecas, executáveis e outros recursos.
    3. **build:** Pasta onde são armazenados os arquivos de compilação do ROS2, incluindo arquivos intermediários e temporários gerados durante o processo de compilação.
    4. **log:** Pasta onde são armazenados os arquivos de log do ROS2, incluindo mensagens de erro, avisos e informações de depuração.

- **Pastas dentro do workspace não são pacotes.** Os pacotes residem dentro dessas pastas (especificamente na pasta src). Cada pacote é uma unidade de código que pode ser compilada e executada independentemente, enquanto as pastas do workspace são usadas para organizar e gerenciar os pacotes e outros recursos do ROS2.



## 1.5 Launch files (Arquivos de lançamento):

- **Em vez de ficar usando vários comandos no terminal para fazer as coisas, escrevemos um arquivo python (launch file) que contém todos os comandos necessários para iniciar um conjunto de nós, com seus parâmetros**. Os tópicos, serviços e ações não são criados pelo launch, e sim pelos nós que ele inicia. Isso permite que o sistema seja iniciado de forma consistente e reproduzível, sem a necessidade de lembrar de todos os comandos e parâmetros necessários. Para isso, em vez de rodar `ros2 run turtlesim turtlesim_node` duas vezes e depois `ros2 run turtlesim mimic`, podemos criar um arquivo de lançamento que inicia os três nós ao mesmo tempo, com os parâmetros necessários (é o exemplo no fim desta seção), e usar `ros2 launch meu_pacote meu_arquivo_de_lancamento.py` para iniciar o sistema. O launch precisa estar dentro de um pacote ou ser passado pelo caminho completo.

- Um launch file fica dentro de um pacote (na pasta `launch/`) ou em qualquer caminho, e é **iniciado** com `ros2 launch <nome_do_pacote> <nome_do_arquivo_de_lancamento.py>` (ou `ros2 launch /caminho/completo/arquivo.launch.py`). Para saber se está rodando, olhamos os logs (cada programa tem um prefixo, como `[gazebo-1]`) e usamos `ros2 node list`.

- Exemplo no sistema atual: 
    - `sim_headless.launch.py` (em `infra/docker/`) - inicia só o servidor do Gazebo, sem interface gráfica, e a ponte do relógio. Não cria o robô nem o Nav2. É uma cópia modificada do `sim.launch.py` do `turtlebot4_gz_bringup`, usada pelo `run_sim_headless.sh`.
    - `turtlebot4_gz.launch.py` (do pacote `turtlebot4_gz_bringup`) - o launch de topo do Gazebo: sobe o simulador, o robô e, se pedido, o Nav2, o SLAM e o RViz.
    - `tb4_loopback_simulation.launch.py` (do pacote `nav2_bringup`) - sobe o Nav2 e o simulador leve.


- **No nosso sistema usamos scripts .sh em volta dos launch files**. O `treino_leve.sh` roda um launch file (o do Nav2 com o simulador leve), depois a base e bateria falsas (um script solto, `fake_tb4_base.py`) e o `patrol_loop` (um `ros2 run`), com `sleep` para esperar o Nav2 subir. O `run_sim_headless.sh` roda o Gazebo sem interface. Já o `ros.sh` não roda launch file: só abre um terminal dentro do container, com o ROS 2 Jazzy e as dependências instaladas.

- **Nós** são criados por programação (um executável vira um nó ao rodar) e também são iniciados por launch files. Arquivos YAML não criam nós: eles guardam os **parâmetros**, que o nó lê ao iniciar. Assim dá para alterar o comportamento de um nó sem recompilar o código.

**Exemplo launch file**: Na pasta estudo/anotações_humanas/exemplo_turtlesim.launch.py que inicia 3 progamas de uma vez, turtlesim_node em /turtlesim1, turtlesim_node em /turtlesim2 e mimic. Para rodar ele: 

``` bash
#Como o container só enxerga a pasta workspace/, copie o arquivo para lá:
cp estudo/anotações_humanas/exemplo_turtlesim.launch.py workspace/

#Dentro do container (infra/docker/ros.sh):

ros2 launch /workspace/exemplo_turtlesim.launch.py

#Em outra aba, mande a primeira andar em círculo e veja a segunda imitar:

ros2 topic pub -r 1 /turtlesim1/turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 1.8}}"
```

# ======================================================================================================
## 2. Como rodar: 
``` bash 
cd ~/dev/physical_ai
infra/docker/ros.sh #entrar no terminal do docker, com ROS 2 jazzy e todas as dependencias instaladas. Para sair utilize "exit", e para parar (rodando fora do container, no seu terminal), utilize "infra/docker/ros.sh parar"

ros2 run turtlesim turtlesim_node # roda o simulador do turtlesim, que é um robô virtual que se move em uma tela.

ros2 run turtlesim turtle_teleop_key # Deve ser usado em outro terminal. Roda o teleop do turtlesim, que permite controlar o robô virtual usando o teclado. Use as setas do teclado para mover o robô.

#para patrol_loop
infra/docker/treino_leve.sh iniciar --rviz --patrulha # inicia o simulador leve e a patrulha
infra/docker/treino_leve.sh terminal # entra no terminal do container


#para abrir o gazebo 
cd ~/dev/physical_ai
# 1. liberar o X11 para o container desenhar a janela
xhost +SI:localuser:root

# 2. subir o Gazebo (mundo vazio, TurtleBot 4, sem Nav2 e sem RViz)
docker run -d --name tb4gui --init --memory=3500m --memory-swap=3500m --cpus=4 \
  --device /dev/dri -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  physical-ai:jazzy bash -c '
    source /opt/ros/jazzy/setup.bash
    ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py \
      world:=empty rviz:=false slam:=false localization:=false nav2:=false'

#Entrar no container para mexer no robô

docker exec -it tb4gui bash -c "source /opt/ros/jazzy/setup.bash; exec bash"

#Dentro dele:

ros2 topic list                                   # tópicos do robô
ros2 topic info /cmd_vel                          # confira o tipo antes de publicar
ros2 topic echo /odom --field pose.pose.position  # posição

#Desligar

docker rm -f tb4gui
xhost -SI:localuser:root
```


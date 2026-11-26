# Comandos básicos do projeto

> **Outro robô:** os exemplos usam o `robot1`. Para outro, rode antes `infra/docker/lab.sh robo usar <nome>` e, nos comandos digitados, troque `/robot1` e o IP pelos dele (`docs/guias/acesso-ao-robo.md`, seção "Vários robôs").

Cola rápida. Todos os comandos partem da raiz do projeto, no PC do laboratório (`cd ~/physical_ai`). Índice dos guias: `docs/guias/como-rodar.md`.

Sequências prontas: `docs/guias/patrulha-volta-a-doca.md` e `docs/guias/patrulha-loop-continuo.md`.

Marcas usadas: **[move]** = o robô real anda. Exige pessoa ao lado e área livre.

## Rede e acesso ao robô

```bash
infra/docker/lab.sh robo checar-rede              # só lê: rotas e se scan, tf e odom chegam ao PC
ping -c 5 192.168.7.7                             # o robô responde pelo Wi-Fi?
ssh robo-wifi                                     # entra no robô pelo Wi-Fi
ssh robo                                          # entra no robô pelo cabo
ip -br addr                                       # IPs e placas de rede (no PC ou no robô)
infra/docker/lab.sh robo usar robot3              # troca de robô: rotas do PC (sudo) e teste
nmcli -t -f NAME,DEVICE connection show --active  # qual rede o PC está usando
cat infra/lab/rede_lab.env infra/lab/robos/robot1.env   # rede comum; domínio, discovery e namespace do robô
```

Dentro do robô (depois do `ssh`):

```bash
systemctl status turtlebot4                       # o serviço ROS do robô está ativo?
ros2 daemon stop; ros2 daemon start; ros2 topic list   # recupera a lista de tópicos incompleta
date                                              # comparar o relógio com o do PC
```

Rotas e acesso: `docs/guias/acesso-ao-robo.md`.

## Subir serviços (robô real)

```bash
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao   # AMCL + mapa (necessário para navegar)
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2 rviz     # navegação + janela do RViz
infra/docker/lab.sh robo subir rviz                                         # só a janela do RViz
infra/docker/lab.sh robo subir slam rviz                                    # mapear (nunca junto da localizacao)
```

## Ver o estado e os logs

```bash
infra/docker/lab.sh robo estado                   # serviços do modo robo em execução
docker ps                                         # todos os contêineres em execução, inclusive os "run"
docker stats --no-stream                          # CPU e memória de cada contêiner
infra/docker/lab.sh robo logs nav2                # últimas 40 linhas do Nav2
infra/docker/lab.sh robo logs localizacao         # últimas 40 linhas do AMCL e do mapa
infra/docker/lab.sh robo logs -f nav2             # acompanha ao vivo (Ctrl+C só fecha o log)
docker logs tb4-robo-nav2-1 2>&1 | grep -E "Managed nodes are active|Aborting bringup|CRITICAL"   # Nav2 ativo?
docker logs tb4-robo-nav2-1 2>&1 | grep -E "Resizing|no map received"                             # o mapa chegou ao Nav2?
docker logs tb4-robo-localizacao-1 2>&1 | grep -E "Setting pose|CRITICAL"                         # pose marcada? AMCL caiu?
```

## Descer contêineres

```bash
infra/docker/lab.sh robo parar                    # derruba TUDO do modo robo (mesmo se passar um nome depois)
infra/docker/lab.sh robo compose rm -sf nav2      # remove só um serviço (aqui, o nav2)
infra/docker/lab.sh sim parar                     # derruba o simulador
docker stop NOME                                  # para um contêiner solto (nome visto no docker ps)
```

Evitar no modo robo, pelos problemas vistos em 23/11: `docker restart` no Nav2 (voltou sem o mapa global) e `docker pause` no RViz (houve quedas de nós logo depois; a causa não foi determinada).

## Sensores e estado do robô (só leitura)

Cada comando abre um contêiner temporário, por isso demora alguns segundos.

```bash
# Todos os tópicos que chegam ao PC
infra/docker/lab.sh robo compose run --rm -T ferramentas ros2 topic list

# Está na doca? Vê a doca? (campos is_docked e dock_visible)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    ros2 topic echo --once /robot1/dock_status irobot_create_msgs/msg/DockStatus --qos-profile sensor_data

# Bateria, de 0 a 1 (0.78 = 78%)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    ros2 topic echo --once /robot1/battery_state sensor_msgs/msg/BatteryState --qos-profile sensor_data --field percentage

# Frequência do lidar (cerca de 8 Hz em 25/11); encerra sozinho em 20 s
infra/docker/lab.sh robo compose run --rm -T ferramentas timeout 20 ros2 topic hz /robot1/scan

# Frequência da odometria (cerca de 20 Hz em 25/11); encerra sozinho em 20 s
infra/docker/lab.sh robo compose run --rm -T ferramentas timeout 20 ros2 topic hz /robot1/odom
```

## RViz

| Ferramenta | Uso |
|---|---|
| 2D Pose Estimate | Informa ao AMCL onde o robô está. Fazer depois de subir a localização |
| Publish Point | Mostra as coordenadas de um ponto do mapa (comando abaixo) |
| Nav2 Goal | **[move]** Envia o robô a um destino |

```bash
# Escuta os cliques do Publish Point (deixar rodando; clicar no mapa; Ctrl+C encerra)
infra/docker/lab.sh robo compose exec -T rviz bash -lc \
    'source /opt/ros/humble/setup.bash; ros2 topic echo /robot1/clicked_point geometry_msgs/msg/PointStamped'
```

## Programas de patrulha **[move]**

Precisam de localização, Nav2 e pose marcada. Passo a passo nos dois guias do topo.

```bash
# 1-2-3-4-3-2-1 e volta à doca (não pede SIM)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop2.py --ros-args -r __ns:=/robot1

# Loop contínuo 1-3-4-3-1 (não pede SIM)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/loop.py --ros-args -r __ns:=/robot1

# Só voltar à doca (não pede SIM)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop2.py --voltar-doca --ros-args -r __ns:=/robot1

# 1-2-3-4 e doca, com checagens e confirmação SIM
workspace/patrulha_oficial/rodar.sh 1
```

A patrulha própria da equipe (`patrulha_tb4`, com arquivo de configuração) é outro programa: seção 6 de `docs/guias/como-rodar.md`.

## Mapa

```bash
infra/docker/lab.sh robo subir slam rviz          # começa o mapeamento (robô partindo da doca)
infra/docker/lab.sh robo teleop                   # [move] dirige pelo teclado; pede SIM
infra/docker/lab.sh robo salvar nome_do_mapa      # grava em workspace/mapas/ (o slam precisa estar rodando)
infra/docker/lab.sh conferir workspace/mapas/mapa_lab_novo.yaml   # confere um mapa salvo, sem ROS
```

## Simulador (não alcança o robô real)

```bash
infra/docker/lab.sh sim subir gazebo slam rviz    # Gazebo para mapear
infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz        # Gazebo para navegar
infra/docker/lab.sh sim undock                    # tira o robô simulado da doca
infra/docker/lab.sh sim teleop                    # dirige o robô simulado
infra/docker/lab.sh sim patrulha                  # patrulha própria no simulador
infra/docker/lab.sh sim parar                     # desliga o simulador
```

Os modos `sim` e `robo` não rodam juntos: pare um antes de subir o outro.

## LLM (linguagem natural)

Sequência completa, na ordem: `docs/guias/llm-linguagem-natural.md`.

```bash
# NO ROBÔ (antes: localizacao, 2D Pose Estimate e nav2; bateria a partir de 0.20)
infra/docker/lab.sh robo llm                      # nó com o freio ligado (não move)
PARKING_BRAKE=false infra/docker/lab.sh robo llm  # [move] pede SIM
infra/docker/lab.sh robo falar                    # enviar pedidos; Enter vazio: pare

# SEM ROBÔ (nunca move: não alcança o robô)
docker compose -f infra/compose/llm.yaml up -d    # inicia o ensaio
docker compose -f infra/compose/llm.yaml logs -f llm      # decisões do nó
docker compose -f infra/compose/llm.yaml exec llm bash -c \
  'source /opt/ros/humble/setup.bash; ros2 topic pub --once -w 1 /robot1/user_input std_msgs/msg/String "data: vai pra janela"'
docker compose -f infra/compose/llm.yaml down     # encerra o ensaio

# modelo
ollama list                                       # modelos baixados
systemctl status ollama                           # serviço ativo?
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.interpretador "vai pra geladeira")   # sem ROS
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar)   # mede acertos e tempo
```

## Imagens e testes

```bash
infra/docker/construir_imagem.sh base robo sim    # constrói as imagens Humble (só no PC do lab)
docker images 'physical-ai'                       # imagens existentes
(cd workspace/meu_ws/src/patrulha_tb4 && python3 -m pytest -q)    # testes da lógica (precisa de pytest; ausente no PC do lab em 25/11)
infra/docker/teste_l1.sh lista                    # cenários de falha no simulador leve
python3 infra/ferramentas/checar_caminhos.py      # os caminhos citados nos documentos existem?
```

# Tarefa: ligar o PC do laboratório ao robô real (rede, Wi-Fi e namespace)

**Aviso (2026-11-16, 22:58): não use o `lab.sh robo` até a imagem Humble existir.** Os nós Jazzy do PC derrubam o robô Humble: ele morreu por falta de memória quando o `slam` e o `rviz` subiram. Explicação e plano: `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md`, seção 8.

**Data:** 2026-11-16 (noite)
**Pedido:** fazer o `lab.sh` funcionar no PC do laboratório, primeiro no Gazebo e depois com o TurtleBot 4 real, entrar no robô por cabo e por Wi-Fi, e adaptar o PC ao robô (opção escolhida pelo Roberto: mudar o PC, não o robô). O robô fica em Humble e o PC em Jazzy: a equipe disse que isso não tem problema.
**Situação:** o Gazebo rodou e salvou um mapa. O robô entra no Wi-Fi e aceita `ssh`. **Com as rotas criadas pelo Roberto, o `checar-rede` deu `REDE OK`**, e os dados chegam ao PC: `/robot1/scan` a 8,4 Hz, `/robot1/odom` a 21,4 Hz e `/robot1/battery_state` a 0,2 Hz (seção 7). **Nada foi enviado para mover o robô.**
**Tarefas anteriores:** `docs/tarefas/2026-11-16-modo-slam.md` e `docs/tarefas/2026-11-16-compose-e-alvos.md`.

## 1. Resposta direta

O PC não enxergava nenhum tópico do robô por quatro motivos, um em cima do outro:

1. **A imagem `physical-ai:base` não existia.** O container do teste nem subia, e o `checar-rede` escondia o erro e dizia "rede reprovada".
2. **O PC estava em Simple Discovery, e o robô usa Discovery Server.** Corrigido no `infra/lab/rede_lab.env`.
3. **O robô publica tudo em `/robot1`.** O PC procurava `/scan`, e o tópico é `/robot1/scan`. Todos os serviços do `robo.yaml` agora recebem `namespace:=/robot1`.
4. **Faltavam rotas no PC.** O DDS do robô anuncia também os endereços do cabo e da USB com a Create 3. O PC responde neles, as respostas se perdiam no roteador e a descoberta nunca terminava. Com duas rotas pelo IP do robô, criadas pelo Roberto com `sudo`, a rede passou.

Também apareceu uma incompatibilidade real entre Humble e Jazzy: o `cmd_vel` do robô é `Twist`, sem carimbo de tempo, e o Jazzy publica `TwistStamped`. O teleop e o Nav2 do modo `robo` agora usam `Twist`. Sem isso, o robô ignoraria todo comando de velocidade.

## 2. O exemplo do dia a dia

É como ligar para um prédio com ramais. Primeiro faltava o telefone (a imagem). Depois o número estava errado (o modo de discovery). Depois pedíamos a sala "scan", e o nome certo é "robot1/scan" (o namespace). Por fim, a portaria atende, mas passa para quem ligou números de retorno de ramais internos do prédio. O PC liga de volta para esses números pela rua, e ninguém atende. A rota diz ao PC: "esses ramais, chame pela portaria".

## 3. O que foi medido no robô

Tudo lido no robô por `ssh`, só leitura, exceto o Wi-Fi (seção 4.5).

| O quê | Valor | Onde foi lido |
|---|---|---|
| Sistema e ROS | Ubuntu 22.04, ROS 2 **Humble** | `/opt/ros/humble`, pacotes `ros-humble-turtlebot4-*` 1.0.x |
| Discovery | Servidor no próprio robô: `fast-discovery-server -i 1 -p 11811`, escutando em `0.0.0.0` | `ps`, `ss -lunp` |
| Variáveis do robô | `ROS_DOMAIN_ID=0`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROS_DISCOVERY_SERVER=";127.0.0.1:11811;"` | `/etc/turtlebot4/setup.bash` |
| Perfil do FastDDS | Vazio (padrão, sem restrição de interface) | `/etc/turtlebot4/fastdds_rpi.xml` |
| Namespace | `/robot1` em todos os nós | `ps` (`-r __ns:=/robot1`) e `ros2 topic list` |
| Tipos | `/robot1/cmd_vel` é `geometry_msgs/msg/Twist`. `scan`, `odom`, `tf`, `tf_static`, `battery_state` e `dock_status` têm os tipos de sempre | `ros2 topic list -t` como super cliente |
| Ações | `/robot1/dock`, `/robot1/undock` e as outras da Create 3 | `ros2 action list` |
| Endereços | `eth0` 192.168.185.3 (cabo), `usb0` 192.168.186.3 (Create 3 em 192.168.186.2), `wlan0` 192.168.7.7 (Wi-Fi) | `ip -br addr` |
| Firewall | `ufw` inativo | `ufw status` |
| Câmera | `OAK-D-PRO`, indício de que o modelo é o padrão (não o Lite) | log do serviço `turtlebot4` |

## 4. As peças, uma por uma

### 4.1 Docker no PC do laboratório

- **Permissão:** o usuário `robotica` não estava no grupo `docker`. O `construir_imagem.sh` dizia "o Docker não está respondendo", mas o Docker estava ligado. Corrigido pelo Roberto com `sudo usermod -aG docker $USER` e um novo login.
- **Compose:** o `docker.io` do Ubuntu 24.04 não traz o plugin `compose`, e o `lab.sh` dava `unknown shorthand flag: 'f'`. Corrigido com `sudo apt install docker-compose-v2`.
- **Imagem `base`:** o `robo.yaml` usa `physical-ai:base` em quase todos os serviços, mas só `robo` e `sim` tinham sido construídas. **Paliativo:** `docker tag physical-ai:robo physical-ai:base` (a `robo` é construída a partir da `base`, então tem tudo que a `base` tem). Por isso as duas aparecem com o mesmo ID. Para ter a base de verdade: `./construir_imagem.sh base`. O `como_rodar.md` agora manda construir `base robo sim`.

### 4.2 Gazebo (modo `sim`)

- **Janela do Gazebo:** não existe, de propósito. O `sim.yaml` roda o Gazebo só como servidor, numa tela falsa. A visão de trabalho é o RViz.
- **Salvar o mapa:** a primeira tentativa falhou com `result=255` (`map_saver: Failed to spin map subscription`). O `/map` estava sendo publicado a 1 Hz, mas o `map_saver` assina com QoS `VOLATILE` e espera só 2 s. Uma nova tentativa salvou: `workspace/mapas/teste_maze.yaml`, `.pgm` e `.info.txt`, às 18:27. O `conferir_mapa` diz `UTILIZÁVEL`, com 17 m x 15 m, 25 % livre. Se a falha voltar, a correção é o `map_saver_cli` com `map_subscribe_transient_local:=true` (não foi feito).

### 4.3 Acesso ao robô

Por cabo (IP fixo `192.168.185.10` no PC, `ssh robo`) e por Wi-Fi (`ssh robo-wifi`, `192.168.7.7`). Os passos e os cuidados estão em `docs/acesso-ao-robo-por-cabo.md`.

### 4.4 Wi-Fi do robô

O robô não se mantinha na `PixelLab-5GHz`: ele conecta, cai cerca de 20 s depois e não acha mais a rede, que fica no canal 157. O robô não enxerga nenhum canal de 5 GHz acima do 149. Fixar o país `BR` não resolveu. O robô foi para a `PixelLab-2.4GHz`, que funcionou. A causa do 5 GHz continua em aberto.

### 4.5 Mudanças feitas no robô

Feitas a pedido do Roberto, como exige o `contexto/AGENTES.md`, seção 1:

- `/etc/modprobe.d/cfg80211-br.conf` (`options cfg80211 ieee80211_regdom=BR`). Não resolveu o 5 GHz, mas é inofensivo e pode ser apagado.
- Perfil do NetworkManager `PixelLab-2.4GHz` (`nmcli device wifi connect`). Fica fora do netplan que o `turtlebot4-setup` gera. Um "Apply Settings" no menu pode recriar o netplan só com o 5 GHz.

Nada mais foi alterado no robô: nem discovery, nem namespace, nem `ROS_DOMAIN_ID`. O perfil `PixelLab-2.4GHz` que uma tentativa anterior deixou com a senha errada foi apagado.

### 4.6 Discovery Server no PC (`infra/lab/rede_lab.env`)

- `ROS_DISCOVERY_SERVER=;192.168.7.7:11811;`. O `;` antes do IP põe o servidor na posição 1, que é o id do servidor do robô (`-i 1`). A posição na lista tem que bater com o id ([manual](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html)).
- `ROS_SUPER_CLIENT=True`. Com Discovery Server, um cliente comum só fica sabendo dos tópicos que ele mesmo usa. O `ros2 topic list` precisa ser super cliente para ver todos.

### 4.7 Rotas no PC

Medido com `tcpdump` no PC, em 20 s de descoberta:

| Destino dos pacotes do PC | Pacotes |
|---|---|
| 192.168.185.3 (cabo do robô) | 545 |
| 192.168.186.3 (USB da Create 3 no robô) | 545 |
| 192.168.186.2 (Create 3) | 35 |
| 192.168.7.7 (Wi-Fi do robô) | 33 |

No sentido contrário, o servidor mandou 1755 pacotes ao PC, com os mesmos tamanhos repetidos dezenas de vezes. São retransmissões: as confirmações do PC iam para os endereços errados. O PC chegou a mostrar `RcvbufErrors` subindo, mas a maior parte dos pacotes era recebida. Não é a causa principal.

Três testes descartaram outras causas:

- No próprio robô, um cliente pelo IP do Wi-Fi (`;192.168.7.7:11811;`) vê os 31 tópicos. O servidor funciona por qualquer endereço.
- Um cliente **Humble** no PC (`ros:humble-ros-base`) também não vê nada. Não é a diferença de versão.
- O PC não filtra a entrada: as regras `nft` e `iptables-legacy` não têm cadeia de entrada.

A correção é uma rota pelo robô para as duas sub-redes. O manual prevê a da Create 3 (`192.168.186.0/24`). A do cabo existe porque o robô mantém o IP do `eth0` mesmo sem o cabo. Os comandos estão na seção 6.

### 4.8 Namespace `/robot1` no PC (opção 2: o PC se adapta)

O namespace vem da variável `ROBO_NS`. O padrão é `/robot1`. `ROBO_NS=` (vazio) serve para um robô sem namespace. A forma `${ROBO_NS-/robot1}` do Compose distingue "não definida" de "vazia".

| Serviço | O que mudou | Conferido |
|---|---|---|
| `slam`, `localizacao`, `nav2`, `rviz` | `namespace:=${ROBO_NS-/robot1}` nos launches oficiais | Os quatro aceitam `namespace` (`ros2 launch ... --show-args` na imagem). O perfil do Nav2 só usa nomes relativos (`scan`, `odom`), que entram no namespace |
| `teleop` | `-r __ns:=/robot1`, omitido quando o namespace é vazio (o ROS recusa `__ns:=` vazio) | Num container **sem rede**, o teleop publicou `/robot1/cmd_vel [geometry_msgs/msg/Twist]` |
| `patrulha` | Argumento novo `namespace` no `patrulha.launch.py`, e o `TurtleBot4Navigator` recebe o namespace do nó monitor | O nó subiu como `robot1.patrulha_monitor`. Testes L0: 128 passaram, 2 pulados (como antes) |
| `lab.sh checar-rede` | Procura `$ROBO_NS/scan`, `/tf` e `/odom` | Rodado de verdade: reprova nas rotas, com o comando para corrigir |

### 4.9 `cmd_vel` sem carimbo (Humble)

O robô Humble só aceita `geometry_msgs/msg/Twist`. No modo `robo`, o padrão do `STAMPED` passou a ser `false`:

- **teleop:** `stamped:=false`.
- **Nav2:** o `nav2_inf_devagar.yaml` tem `enable_stamped_cmd_vel: true`, que é o certo para o Gazebo Jazzy e para o simulador leve. O serviço `nav2` do `robo.yaml` faz uma cópia em `/tmp` trocando o valor pelo `STAMPED` e lança com ela. Assim o perfil continua sendo um arquivo só. O `sim.yaml` não mudou.

### 4.10 `checar-rede` mais honesto

- Confere as rotas antes de testar o DDS. Se faltarem, reprova e mostra o comando `nmcli` com o nome da conexão Wi-Fi em uso.
- Se o container de teste não sobe (imagem faltando, Docker sem permissão), mostra o erro em vez de "rede reprovada".
- Faz 4 listagens com 4 s de intervalo (antes eram 3 com 3 s). No próprio robô, os 31 tópicos levaram cerca de 10 s para aparecer.

### 4.11 Erros de documentação corrigidos

- O `como_rodar.md` mandava usar `cd ~/dev/physical_ai/...`. No PC do lab, o caminho é `~/physical_ai/...`.
- O `./lab.sh conferir ../../workspace/...` nunca funcionava, porque o `lab.sh` vai para a pasta `Roberto/` antes. O certo é `workspace/mapas/...`.
- O kit de campo mandava usar `stamped:=true` e nomes sem namespace no robô real.

## 5. Arquivos mexidos

| Arquivo | Mudança |
|---|---|
| `infra/compose/robo.yaml` | Namespace em todos os serviços, `STAMPED=false`, cópia do perfil do Nav2, cabeçalho explicando o robô do lab |
| `infra/docker/lab.sh` | `checar_rotas`, `checar_rede` com namespace e erro visível, `ROBO_NS` na ajuda |
| `infra/lab/rede_lab.env` | Discovery Server do robô, super cliente e aviso das rotas |
| `workspace/meu_ws/src/patrulha_tb4/launch/patrulha.launch.py` | Argumento `namespace` |
| `workspace/meu_ws/src/patrulha_tb4/patrulha_tb4/no_patrulha.py` | `TurtleBot4Navigator(namespace=...)` |
| `docs/acesso-ao-robo-por-cabo.md` | Cabo e Wi-Fi confirmados, causa do 5 GHz, seção de rotas, registro da autorização |
| `specs/patrol-inf/kit-de-campo.md` | Caixa do robô do lab na etapa 1, `/robot1` nas etapas 1, 3 e 10, `stamped:=false`, folha de anotações |
| `como_rodar.md`, `contexto/pendencias.md`, `docs/tarefas/2026-11-16-compose-e-alvos.md`, `docs/registro-de-mudancas.md` | Estado e caminhos |
| `~/.ssh/config` (fora do repositório) | Apelidos `robo` e `robo-wifi` |

## 6. Como usar no laboratório

1. **Uma vez, criar as rotas** (já feito em 2026-11-16 na conexão `PixelLab-2.4GHz`; o `checar-rede` mostra o comando se faltarem):
   ```
   sudo nmcli connection modify "PixelLab-2.4GHz" +ipv4.routes "192.168.186.0/24 192.168.7.7 500, 192.168.185.0/24 192.168.7.7 500"
   sudo nmcli connection up "PixelLab-2.4GHz"
   ```
2. `cd ~/physical_ai/Roberto/infra/docker` e `./lab.sh robo checar-rede`. Espere `REDE OK: /robot1/scan, /robot1/tf e /robot1/odom`. Se aparecer `permission denied` no Docker, o terminal é anterior ao `usermod`: rode `newgrp docker` ou entre de novo na sessão.
3. Daí em diante, o roteiro do `como_rodar.md` e do kit de campo (etapas 1 a 4) vale como está: `./lab.sh robo subir slam rviz`, e o teleop só com alguém ao lado.

## 7. O que foi e o que não foi verificado

| Afirmação | Situação |
|---|---|
| O robô é Humble, usa Discovery Server id 1, domínio 0 e namespace `/robot1` | **Medido** no robô |
| `/robot1/cmd_vel` é `Twist` | **Medido** (`ros2 topic list -t` no robô) |
| A causa da descoberta falhar no PC são as respostas para 192.168.185.x e 192.168.186.x | **Medido** com `tcpdump`, e **confirmado**: com as rotas, `REDE OK` |
| Os dados do robô chegam ao PC | **Medido** no PC: `/robot1/scan` 8,4 Hz, `/robot1/odom` 21,4 Hz, `/robot1/battery_state` 0,2 Hz (uma a cada 5 s), bateria em 100 % |
| Os launches oficiais aceitam `namespace` | **Conferido** com `--show-args` na imagem |
| O teleop publica `Twist` em `/robot1/cmd_vel` | **Medido**, num container sem rede (nada chegou ao robô) |
| A patrulha sobe no namespace | **Medido** (`robot1.patrulha_monitor`). Patrulha com o robô: **não rodada** |
| Nav2 Jazzy com `enable_stamped_cmd_vel: false` move o robô Humble | **Não testado** |
| `Dock`, `Undock` e `DockStatus` funcionam entre Humble e Jazzy | **Não testado**. As ações existem no robô com esses nomes |
| O robô volta sozinho ao Wi-Fi depois de reiniciar | **Não testado** |
| SLAM no Gazebo pelo Compose | **Medido**: `teste_maze`, `UTILIZÁVEL` |

## 8. Descoberta: Jazzy no PC derruba o robô Humble

**Medido em 2026-11-16, 22:58.** A equipe tinha dito que Humble no robô e Jazzy no PC não dava problema. Dá.

1. 22:58:11: o Roberto subiu `slam` e `rviz` no PC (Jazzy).
2. 22:58:14: os nós Humble do robô começaram a falhar ao ler uma mensagem interna do ROS 2 (o tópico `ros_discovery_info`, que anuncia os nós de cada processo):
   ```
   'Bad alloc' exception deserializing message of type rmw_dds_common::msg::dds_::ParticipantEntitiesInfo_
   ```
3. 22:58:20: o kernel matou o `joint_state_publisher` (585 MB de memória) e depois o serviço `turtlebot4` inteiro (`Failed with result 'oom-kill'`). O robô ficou sem lidar, sem TF e sem odometria. Só o servidor de discovery continuou vivo.

**Por quê:** a mensagem `ParticipantEntitiesInfo` mudou de formato depois do Humble (o identificador dos participantes ficou menor). O Humble lê a do Jazzy com o formato antigo, entende um tamanho absurdo e tenta alocar memória demais. O ROS 2 não garante comunicação entre distribuições diferentes. Os testes com poucos nós Jazzy (`ros2 topic list`, `topic hz`) não derrubaram o robô. Com o SLAM e o RViz, a carga foi maior. **Qualquer nó Jazzy na rede do robô pode derrubá-lo**, inclusive o `checar-rede`.

**Isto também explica** o SLAM sem `/robot1/map` e sem o frame `odom`: o robô já tinha caído.

**Demanda registrada (decisão do Roberto, 2026-11-16): fazer o modo `robo` do PC em Humble.** O robô fica como está, e o `sim` continua em Jazzy. O trabalho previsto:

- Um alvo novo no `infra/docker/Dockerfile` (por exemplo `robo-humble`, a partir de `ros:humble-ros-base`, já baixada no PC), com os pacotes `ros-humble-turtlebot4-*`, slam_toolbox, Nav2, `turtlebot4_viz`/RViz e `teleop_twist_keyboard` do Humble.
- No `infra/compose/robo.yaml`, trocar a imagem e o `source /opt/ros/jazzy` pelo Humble. O `STAMPED=false` deixa de ser exceção: no Humble, o `Twist` é o padrão. A cópia do perfil do Nav2 com `enable_stamped_cmd_vel: false` continua, ou o perfil do Humble é gerado à parte (conferir os parâmetros do Nav2 Humble, que diferem do Jazzy).
- Conferir no Humble os argumentos `namespace` dos launches (`--show-args`), o `TurtleBot4Navigator` e o `BasicNavigator` usados pela patrulha, e rodar os testes L0 na imagem nova.
- Só depois: reiniciar o serviço do robô (`sudo systemctl restart turtlebot4`, ou desligar e ligar), `checar-rede`, e o SLAM acompanhando a memória do robô (`free -m`).

A alternativa, atualizar o robô para Jazzy, é decisão da equipe do INF.

**Estado deixado em 2026-11-16, 20:07 (hora do PC):** nenhum container no PC, a permissão de tela do RViz retirada, e o Raspberry Pi do robô desligado (`sudo shutdown -h now`). Para religar, siga o manual do robô (botão de energia, ou tirar da doca e recolocar). As rotas do PC e o `rede_lab.env` ficaram como estão.

## 9. Efeito prático

A rede entre o PC e o robô funciona, mas o modo `robo` precisa ir para Humble antes de qualquer uso (seção 8). Depois disso, mapear o laboratório é o mesmo roteiro do Gazebo, com `robo` no lugar de `sim`. O teleop e o Nav2 já falam a língua do robô Humble, e todos os nomes já saem com `/robot1`. Se algo falhar, o `checar-rede` diz em qual camada: imagem, rota ou DDS, em vez de um "reprovado" genérico.

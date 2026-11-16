# Tarefa: Docker Compose e imagens em camadas

**Data:** 2026-11-16 (tarde)
**Pedido:** trocar a imagem Docker única por imagens menores, uma para cada tipo de tarefa, e passar a rodar as tarefas por Docker Compose: um serviço para o SLAM, outro para a patrulha, e as outras divisões que fossem necessárias.
**Situação:** arquivos prontos e conferidos sem Docker. **Nada rodou com o Docker de verdade, nem no robô.** No notebook, o Docker estava desligado e havia 1,5 GiB de memória livre. O que foi e o que não foi verificado está na seção 7.
**Tarefa anterior, que esta continua:** `docs/tarefas/2026-11-16-modo-slam.md`

## 1. Resposta direta

Fiz as duas coisas juntas, porque elas resolvem problemas diferentes:

| Ferramenta | Responde a | Arquivo |
|---|---|---|
| **Alvos do Dockerfile** | O que vai dentro de cada imagem | `infra/docker/Dockerfile` |
| **Docker Compose** | Como cada container roda: rede, memória, pastas e comando | `infra/compose/robo.yaml` e `infra/compose/sim.yaml` |

Agora são cinco imagens em camadas (`base`, `robo`, `sim`, `llm` e `completa`) e dois arquivos de serviços, um para o robô real e outro para o Gazebo. Os dois arquivos têm os mesmos nomes de serviço: `slam`, `localizacao`, `nav2`, `rviz`, `teleop` e `patrulha`. O atalho `infra/docker/lab.sh` ficou só com o que o Compose não sabe fazer. Ele substitui o `slam.sh` da manhã.

```bash
./lab.sh robo subir slam rviz      # mapa no robô real
./lab.sh sim  subir gazebo slam    # o mesmo, no Gazebo
```

## 2. O exemplo do dia a dia

Pense numa **cozinha de restaurante**.

- **As imagens são os kits de cada bancada.** Toda bancada tem faca e tábua (a `base`). A de finalização tem também o maçarico (o RViz, na `robo`). Só a de treino dos novatos tem o forno grande (o Gazebo, na `sim`). Ninguém leva o forno grande para a bancada de saladas.
- **O Compose é a escala da cozinha, pregada na parede.** Ela diz quem fica em qual bancada, com qual kit, e quem pode mexer no fogo. Antes, essa escala estava na cabeça do chefe, ou seja, dentro de um script. Agora qualquer um lê.
- **O `lab.sh` é o chefe de cozinha.** Antes de abrir, ele confere se o gás chegou (a rede) e não deixa o treino e o serviço de verdade acontecerem na mesma cozinha ao mesmo tempo (o sim e o robo juntos).

## 3. Antes e depois

| | Manhã (`slam.sh`) | Agora (Compose) |
|---|---|---|
| Imagens | Uma só, com tudo, inclusive o Gazebo | Cinco em camadas. O robô real usa a `base` e a `robo`, sem Gazebo |
| Onde está como cada container roda | Linhas de `docker run` dentro de um script | `robo.yaml` e `sim.yaml`, que a equipe consegue ler |
| Tarefas | SLAM, num container só | SLAM, localização, Nav2, RViz, teleop e patrulha, cada uma no seu container |
| Reiniciar a patrulha | Não existia | Reinicia só a `patrulha`, sem derrubar o Nav2 nem perder a pose |
| Patrulha no robô real | Não existia pelo script | Serviço `patrulha`, com `validar_pontos` e confirmação `SIM` antes |

## 4. O pipeline, peça por peça

### 4.1 As imagens em camadas

| | |
|---|---|
| **Onde** | `infra/docker/Dockerfile` (reescrito) |
| **O que faz** | Define cinco alvos (*targets*). Cada um começa do anterior e acrescenta pacotes |
| **Para quê** | Construir e baixar só o que a tarefa usa |

**O que é um alvo.** É um trecho do Dockerfile que começa com `FROM ... AS <nome>`. O comando `docker build --target robo` constrói só até esse trecho. As imagens que começam umas das outras **dividem as camadas no disco**: a `sim` não guarda uma segunda cópia do ROS, só acrescenta o que é dela.

| Alvo | Imagem | Começa de | Acrescenta | Quem usa |
|---|---|---|---|---|
| `base` | `physical-ai:base` | `ros:jazzy-ros-base` | Nav2, `turtlebot4_navigation`, `slam_toolbox`, `irobot_create_msgs`, teleop, `colcon` e PyYAML | SLAM, localização, Nav2, teleop e patrulha no robô real |
| `robo` | `physical-ai:robo` | `base` | `turtlebot4_desktop` (RViz e `turtlebot4_viz`) | O RViz no lab |
| `sim` | `physical-ai:sim` | `robo` | Gazebo e TurtleBot 4 simulado, simulador leve, Xvfb e o `patrol_loop` oficial | Todo o `sim.yaml` |
| `llm` | `physical-ai:llm` | `base` | Tutoriais oficiais, incluindo o do OpenAI | Esqueleto da missão 2 |
| `completa` | `physical-ai:jazzy` | `sim` | Tutorial do OpenAI | Os scripts do simulador leve (`ros.sh`, `treino_leve.sh` e `teste_l1.sh`) |

Por que cada escolha:

- **A `base` não tem RViz.** O RViz arrasta bibliotecas gráficas (Qt, OpenGL). SLAM, Nav2 e patrulha não abrem janela. Fora do RViz, nenhum serviço do robô precisa delas.
- **A `sim` começa da `robo`.** No Gazebo, você quase sempre quer ver o mapa no RViz.
- **A `completa` mantém o nome antigo, `physical-ai:jazzy`.** Os scripts dos testes L1 usam esse nome. Eles passaram nos 10 cenários, e as evidências estão amarradas a eles. Mudar o nome obrigaria a mexer neles sem ganho nenhum.
- **A `llm` é só um esqueleto.** O provedor de LLM ainda é pendência aberta. Quando ele for decidido, as bibliotecas entram nesse alvo e não tocam no simulador.
- **O peso.** O Gazebo deve ser a maior parte da imagem antiga, mas **não medi**. No PC do lab, `docker images physical-ai` mostra o tamanho de cada imagem. Essa medição está nas pendências.

### 4.2 Construir as imagens

| | |
|---|---|
| **Onde** | `infra/docker/construir_imagem.sh` (reescrito) |
| **O que faz** | `./construir_imagem.sh robo sim` constrói os alvos pedidos. Sem argumento, constrói a `robo`. `todas` constrói os cinco |
| **Para quê** | No lab, começar pelo que o mapa precisa (a `robo`) e construir a `sim` depois |

Ele continua recusando o build com menos de 12 GiB de RAM. O motivo é o mesmo da manhã: o `docker build` não tem teto de memória e já travou o seu notebook.

**No notebook**, há um subcomando novo: `./construir_imagem.sh apelidos`. Ele não constrói nada. Só dá à `physical-ai:jazzy` que você já tem os nomes `base`, `robo` e `sim` (`docker tag`). Isso funciona porque a imagem antiga tem tudo o que essas três têm. Com os apelidos, o Compose acha as imagens no notebook também, se um dia você quiser rodar algo leve lá.

### 4.3 O Docker Compose

**O que é.** O Docker Compose lê um arquivo YAML com uma lista de *serviços*. Cada serviço diz qual imagem usar, com qual comando, qual rede e quanta memória. Para subir um serviço: `docker compose -f <arquivo> up -d <serviço>`. Para rodar um serviço interativo que some ao terminar: `docker compose -f <arquivo> run --rm <serviço>`.

| | |
|---|---|
| **Onde** | `infra/compose/robo.yaml` e `infra/compose/sim.yaml` (novos) |
| **Para quê** | Um serviço por tarefa. A configuração de cada container fica escrita num lugar que se lê, e não espalhada num script |

**Por que dois arquivos, e não um.** A diferença que importa entre o treino e o robô real é a rede, e ela vale para todos os serviços de uma vez. Com dois arquivos, cada um tem a rede certa no topo, e os nomes de serviço são iguais. O que você aprende no Gazebo vale para o robô trocando só `sim` por `robo`.

Os serviços:

| Serviço | O que roda (comando oficial) | Imagem | Teto | Fonte |
|---|---|---|---|---|
| `gazebo` (só sim) | `turtlebot4_gz.launch.py world:=maze`, sem SLAM, localização nem Nav2, sem janela | `sim` | 4 GiB (`MEM_GAZEBO`) | [Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html), seção do simulador |
| `slam` | `slam.launch.py sync:=true` | `base` | 2 GiB | [Generating a map](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/generate_map.html) |
| `localizacao` | `localization.launch.py map:=$MAPA` | `base` | 1 GiB | Navigation |
| `nav2` | `nav2.launch.py params_file:=nav2_inf_devagar.yaml` (no sim, o `nav2.yaml` oficial) | `base` | 2 GiB | Navigation |
| `rviz` | `view_navigation.launch.py` | `robo` | 1 GiB | Generating a map, aba Jazzy |
| `teleop` | `teleop_twist_keyboard`, `stamped:=true`, 0,15 m/s e 0,5 rad/s | `base` | 256 MiB | [Driving](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/driving.html) |
| `patrulha` | `colcon build`, depois `validar_pontos` e `patrulha.launch.py` | `base` | 512 MiB | O nosso pacote |
| `undock` (só sim) | `ros2 action send_goal /undock ...` | `sim` | 256 MiB | [Docking, Create 3](https://iroboteducation.github.io/create3_docs/api/docking/) |
| `ferramentas` | Um terminal ROS (`bash`) | `base` | 512 MiB | |

No `sim.yaml`, todos os serviços usam a imagem `sim` e `use_sim_time:=true` (o relógio do Gazebo). Os tetos de memória são **estimativas, não medidas**. Se um serviço morrer por falta de memória, `./lab.sh <modo> estado` mostra, e o teto se ajusta no arquivo.

Os nomes dos argumentos foram conferidos no código-fonte oficial (ramo `jazzy`). A localização recebe o mapa por `map`. O Nav2 recebe os parâmetros por `params_file`, e não por `params` (o que existe é o `params` da localização, para os parâmetros do AMCL).

**Por que SLAM, localização e Nav2 em serviços separados.** Primeiro, para trocar de tarefa sem derrubar tudo: depois do mapa, você para o `slam` e sobe a `localizacao` e o `nav2`. Segundo, para reiniciar a `patrulha` sem perder o Nav2 e a pose do robô. Atenção: **o `slam` e a `localizacao` não rodam juntos.** Os dois publicam a mesma transformação `map → odom` e brigariam por ela.

**As decisões de segurança dentro dos arquivos, e por quê:**

| Decisão | Por quê |
|---|---|
| Todo serviço tem `profiles` | Um `docker compose up` sem nome de serviço não sobe nada. Sem isso, um `up` distraído subiria todos os serviços, inclusive a patrulha. Cada serviço é chamado pelo nome |
| `teleop` e `patrulha` rodam só com `run` e pedem `SIM` | Os dois movem o robô real. O `run` dá um terminal interativo, onde a pergunta aparece. Pelo `up`, o `lab.sh` recusa e explica |
| A `patrulha` roda o `validar_pontos` antes | É o item 1 do protocolo do INF: sem a configuração aprovada, nenhum movimento autônomo. O valor padrão de `CONFIG` é o modelo vazio, que o `validar_pontos` recusa de propósito |
| Sem `build:` nos arquivos e `pull_policy: never` | O Compose nunca constrói nem baixa imagem sozinho. O build só acontece pelo `construir_imagem.sh`, que confere a RAM. Se a imagem não existir, o Compose dá erro em vez de travar a máquina |
| `robo.yaml`: `network_mode: host` e `env_file: rede_lab.env` | O container usa a rede do PC, onde o robô está, com o domínio e o FastDDS do manual |
| `sim.yaml`: rede isolada **e** `ROS_DOMAIN_ID=42` | São duas barreiras. A rede isolada impede o tráfego de sair. O domínio diferente faz o ROS 2 ignorar mensagens do sim, mesmo que alguma escape. O robô usa o domínio 0 |
| `ipc: host` nos dois arquivos | O FastDDS usa memória compartilhada entre programas da mesma máquina. Com containers separados e `ipc` separado, eles se descobrem, mas os dados não passam. Isso vem da prática de ROS 2 com Docker, e não do manual. No sim, a descoberta continua presa à rede isolada e ao domínio 42 |
| `init: true` | Um processo de init de verdade repassa o `Ctrl+C` à patrulha, que precisa dele para gravar o `resumo` (PAT-15) |
| A `patrulha` compila o pacote em `/tmp` | O `colcon build` leva cerca de 1 s. Compilando em `/tmp`, o root do container não deixa arquivos dele no workspace, e cada execução usa o código atual |
| O socket da tela (`/tmp/.X11-unix`) montado em todos | Só leitura, e não abre nada sozinho. O `xhost`, que dá a permissão da tela, só é chamado quando o `rviz` sobe |

**Duas sintaxes do Compose que aparecem nos arquivos:**

- `${MAPA:-/mapas/lab.yaml}`: use a variável `MAPA` do seu terminal. Se ela não existir, use `/mapas/lab.yaml`. É assim que `MAPA=... ./lab.sh robo subir localizacao` funciona.
- `$$resposta`: o Compose trocaria `$resposta` pelo valor de uma variável do seu terminal. O `$$` diz "deixe o `$` para o bash de dentro do container".

### 4.4 O atalho `lab.sh`

| | |
|---|---|
| **Onde** | `infra/docker/lab.sh` (novo). O `slam.sh` da manhã foi apagado; ele nunca chegou ao git |
| **O que faz** | Chama o Compose no arquivo certo e faz o que o Compose não sabe fazer |

| O que o `lab.sh` faz | Por que o Compose sozinho não faz |
|---|---|
| `checar-rede` antes de `robo subir` | O Compose não tem "só suba se a rede estiver boa". Assim o erro aparece antes do mapa, e não no meio dele |
| Recusa o `robo` com o `sim` ligado, e vice-versa | O Compose não sabe do outro arquivo. Com os dois ligados, fica fácil digitar no terminal errado |
| `xhost` antes do `rviz` | O Compose não roda comandos no seu computador, só nos containers |
| `salvar` | Chama o serviço do `slam_toolbox`, confere o `result=0`, devolve os arquivos ao seu usuário, grava a ficha `.info.txt` (com o hash do git, que só existe fora do container) e roda o `conferir_mapa` |
| Cria `workspace/mapas/` e `workspace/logs/` | Se o Docker criasse essas pastas, elas seriam do root |
| `parar` | Devolve ao seu usuário o que os containers gravaram e desliga todos os serviços do modo |

Para qualquer outra coisa do Compose, há uma porta direta: `./lab.sh robo compose <argumentos>`. Exemplo: `./lab.sh robo compose stop slam`.

### 4.5 A configuração da patrulha mora ao lado do mapa

Achado desta tarefa. Dentro do container, os mapas aparecem em `/mapas/`. No notebook, eles ficam em `workspace/mapas/`. Um caminho absoluto no campo `mapa` só funcionaria num dos dois lugares.

O `config.py:141` resolve o `mapa` **relativo ao arquivo de configuração**. Então a recomendação ficou assim: copie o `config/inf_lab.yaml` para `workspace/mapas/inf_lab_preenchido.yaml` e deixe `mapa: lab.yaml`, que já é o valor do modelo. O mesmo arquivo funciona no container (`CONFIG=/mapas/inf_lab_preenchido.yaml`) e no notebook (`validar_pontos workspace/mapas/inf_lab_preenchido.yaml`). E ele vai para o git junto com o mapa.

### 4.6 Logs

Pelo Compose, a patrulha grava o log JSONL em `workspace/logs/`. Essa pasta está no `.gitignore`, porque cada execução gera arquivos. Copie para `progresso/evidencias/` o que for evidência de aceite, como o kit de campo já pede.

### 4.7 O que ficou como estava, de propósito

| Ficou igual | Por quê |
|---|---|
| `teste_l1.sh`, `l1_dentro.sh`, `treino_leve.sh` e `ros.sh` | Passaram nos 10 cenários do L1, e as evidências estão amarradas a eles. Continuam usando a `physical-ai:jazzy` (alvo `completa`) |
| `rede_lab.env` | O conteúdo é o mesmo. Só o comentário diz quem o lê agora |
| `conferir_mapa` e `workspace/mapas/` | Continuam iguais aos da manhã |

## 5. Arquivos mexidos

| Arquivo | Mudança |
|---|---|
| `infra/docker/Dockerfile` | Reescrito em cinco alvos |
| `infra/docker/construir_imagem.sh` | Build por alvo e subcomando `apelidos` |
| `infra/compose/robo.yaml` | Novo |
| `infra/compose/sim.yaml` | Novo |
| `infra/docker/lab.sh` | Novo, no lugar do `slam.sh` (apagado) |
| `.gitignore` | `workspace/logs/` |
| `specs/patrol-inf/kit-de-campo.md` | Etapas 4, 5 e 7 pelo Compose. A etapa 5 também deixou de dizer que o `nav2_inf_devagar.yaml` não existe: ele existe desde 12/nov |
| `como_rodar.md` | A seção do modo SLAM virou "Modo laboratório: Docker Compose" |
| `contexto/pendencias.md` | Itens atualizados, e um novo: medir o tamanho das imagens no lab |
| `workspace/mapas/README.md` e `infra/lab/rede_lab.env` | Referências ao `lab.sh` e ao Compose |
| `docs/registro-de-mudancas.md` | Entrada "2026-11-16 (tarde)", mudanças 38 a 45 |
| `docs/tarefas/2026-11-16-modo-slam.md` | Aviso no topo, apontando para este documento |

## 6. Como usar no laboratório

```bash
cd ~/dev/physical_ai/Roberto/infra/docker
./construir_imagem.sh robo sim            # 1ª vez no PC do lab

# 1) Treino do mapa no Gazebo
./lab.sh sim subir gazebo slam rviz       # espere cerca de 1 min; ./lab.sh sim logs gazebo
./lab.sh sim compose run --rm ferramentas bash -c 'ros2 topic hz /scan'   # o lidar chega? (Ctrl+C)
./lab.sh sim undock
./lab.sh sim teleop                       # dê uma volta pelo maze
./lab.sh sim salvar teste_maze            # deve dizer UTILIZÁVEL
./lab.sh sim parar

# 2) Mapa do laboratório (antes: kit de campo, etapas 1 a 3, com a pessoa ao lado)
./lab.sh robo checar-rede
./lab.sh robo subir slam rviz             # robô ainda na doca (H3)
#    undock à mão (kit, etapa 3)
./lab.sh robo teleop                      # digite SIM; devagar até o mapa fechar
./lab.sh robo salvar lab
./lab.sh robo compose stop slam

# 3) Pontos e patrulha (kit, etapas 5 a 8)
MAPA=/mapas/lab.yaml ./lab.sh robo subir localizacao nav2 rviz
#    copiar config/inf_lab.yaml para workspace/mapas/inf_lab_preenchido.yaml e preencher
CONFIG=/mapas/inf_lab_preenchido.yaml ./lab.sh robo patrulha   # validar_pontos e SIM antes
./lab.sh robo parar
```

## 7. O que foi e o que não foi verificado

| Item | Situação |
|---|---|
| Os dois arquivos do Compose são válidos | **Medido:** `docker compose config` aceita os dois e lista os serviços. As variáveis (`VEL`, `MAPA`) entram nos comandos e os `$$` chegam ao bash como `$` |
| Lógica do `lab.sh` | **Medida com um `docker` falso:** a rede aprova e reprova; nada sobe com a rede reprovada; recusa o `robo` com o `sim` ligado; `salvar` recusa sem o `slam` e grava mapa, ficha e conferência com ele; `teleop` pelo `subir` e `undock` no `robo` são recusados; `parar` devolve as pastas |
| `construir_imagem.sh` | **Medido:** recusa no notebook pela RAM (7 GiB) e recusa alvo desconhecido. `apelidos` **não rodado** (Docker desligado) |
| Nomes dos argumentos (`map`, `params_file`, `use_sim_time`, `sync`) | **Conferidos** no código-fonte dos launches, ramo `jazzy` |
| `maze.sdf` e `maze.yaml` existem | **Conferido** nos repositórios, ramo `jazzy` |
| `mapa` relativo ao arquivo de configuração | **Conferido** em `config.py:141` |
| Suíte L0 | **Medida:** `130 passed` (nada mudou no Python nesta tarefa) |
| Build dos cinco alvos | **Não verificado:** só no PC do lab |
| Tamanho de cada imagem e o ganho real da divisão | **Não medido** (pendência) |
| Os tetos de memória de cada serviço | **Estimados, não medidos** |
| Containers separados conversando pelo FastDDS com `ipc: host` | **Não verificado** |
| O lidar do Gazebo chega ao `/scan` no `maze` | **Não verificado, e é um risco.** Lendo o código, o arquivo que liga o lidar do Gazebo ao ROS tem `world` com padrão `warehouse`, e o launch do robô não repassa o mundo. Se o `ros2 topic hz /scan` do passo 1 não mostrar mensagens, esse é o primeiro suspeito. Há também a pendência antiga do lidar devolvendo 0,16 m no mundo vazio |
| Ctrl+C na patrulha pelo `docker compose run` chegando ao nó | **Não verificado.** O `init: true` existe para isso. No primeiro teste, confira se o log tem `encerrado` e `resumo` |
| Os mesmos pontos de risco da manhã (`stamped:=true` no Gazebo, Discovery Server) | Continuam **não verificados** (ver o documento do modo SLAM, seção 5) |

## 8. Efeito prático

- **No laboratório**, o primeiro dia fica mais curto. Você constrói só a `robo`, sem o Gazebo, e já pode mapear. A `sim` pode ser construída enquanto você trabalha.
- **Para a equipe**, quem abrir o `robo.yaml` vê, sem ler bash, o que encosta no robô real, com quanta memória e com qual comando oficial. Os serviços que movem o robô estão marcados e pedem confirmação.
- **Para a missão 2**, o LLM ganha lugar pronto: um alvo `llm` no Dockerfile e, quando chegar a hora, mais um serviço no `robo.yaml`.
- **Perguntas que a banca ou o coordenador podem fazer:**
  - "Por que dois arquivos de Compose?" Porque a rede é o que separa treino de robô real, e assim cada arquivo tem uma rede só.
  - "O que impede o simulador de comandar o robô?" A rede isolada e o domínio 42: são duas barreiras independentes.

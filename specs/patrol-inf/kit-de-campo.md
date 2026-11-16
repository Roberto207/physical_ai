# Kit de campo: a patrulha no TurtleBot 4 do INF

**Status:** primeira versão, escrita em 2026-11-12. **Nada daqui foi rodado no robô.** Os comandos vêm da documentação oficial (links em cada etapa), que foi consultada por busca em 2026-11-12. Releia a página indicada antes de rodar cada comando: o manual muda entre versões.
**Base:** `DESIGN.md`, seção 4, e `DEFINE.md`, seção "Protocolo no INF".

## Resposta direta

São 10 etapas, na ordem. Cada uma tem o comando, o critério de "feito" e a página oficial que a embasa. Só passe à etapa seguinte quando a anterior estiver feita. As etapas 1 a 3 não usam o nosso código: servem para saber se a rede, o robô e a doca funcionam. O nosso pacote só entra na etapa 6.

## A cena do dia a dia

É a **lista de verificação de um piloto antes de decolar**. Ele não confere o motor depois de estar no ar. Aqui é igual: primeiro a rede, depois andar com o controle na mão, depois a doca, e só no fim o robô anda sozinho. Se um item falhar, o voo não sai, e ninguém se machuca.

## Regras que valem o tempo todo

| Regra | Por quê |
|---|---|
| Uma pessoa ao lado do robô, pronta para pará-lo, em todo movimento autônomo | Protocolo, item 2. Hardware real não tem "reset" |
| Área livre de pessoas, cabos e objetos baixos | O lidar não vê tudo (pernas de cadeira finas, vidro) |
| Velocidade reduzida (`nav2_inf_devagar.yaml`, 0,15 m/s) nas etapas 5 a 9 | INF-02 |
| `validar_pontos` aprovado antes de qualquer movimento autônomo | Protocolo, item 1. Pega erro de digitação antes de o robô ir para a parede |
| Nenhum comando fora deste kit sem combinar antes | Regra do projeto para o robô físico |

### Como parar o robô

Do mais suave ao mais forte. Combine com a equipe qual usar antes de começar.

1. **`Ctrl+C` no terminal da patrulha.** O nosso nó cancela a ação em andamento, grava o resumo e sai em até 3 s (PAT-15). É a parada normal.
2. **Levantar o robô do chão.** Os sensores de desnível da Create 3 param as rodas. Página: [Safety, Create 3](https://iroboteducation.github.io/create3_docs/api/safety/).
3. **Serviço de parada de emergência da Create 3** (`/e_stop`, descrito na mesma página de Safety). Confira o comando exato na página antes da visita: não foi testado por nós.

Uma parada pelo protocolo de segurança **invalida** a execução de aceite (INF-03). Isso é esperado: repete-se depois.

## Antes de sair de casa

| Item | Feito quando |
|---|---|
| Suíte L0 passando | `cd workspace/meu_ws/src/patrulha_tb4 && python3 -m pytest -q` sem falhas |
| L1 passando no simulador leve | `infra/docker/teste_l1.sh ciclo` diz APROVADO |
| Notebook com o ROS 2 Jazzy e os pacotes `turtlebot4_navigation` e `irobot_create_msgs` | Hoje isso só existe dentro do container `physical-ai:jazzy`, que **não** foi testado falando com um robô real pela rede. Ver "O que falta decidir" |
| Perguntas ao coordenador respondidas | Modelo (Standard ou Lite), números do aceite, rede do laboratório |
| Bateria do robô carregada e doca ligada na tomada | A doca precisa de energia para o robô enxergá-la ([Docking, Create 3](https://iroboteducation.github.io/create3_docs/api/docking/)) |

## As 10 etapas

### 1. Rede: o PC enxerga o robô

Página: [Networking](https://turtlebot.github.io/turtlebot4-user-manual/setup/networking.html), [Simple Discovery](https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html) e [Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html).

O que o manual diz, e que muda o nosso plano:

- No Jazzy, os tópicos da Create 3 chegam ao PC por um nó chamado `create3_republisher`, que roda no Raspberry Pi do robô.
- O modo Simple Discovery usa multicast, e o manual avisa que isso costuma dar problema em redes de universidade. Para navegação, ele recomenda o **Discovery Server**.
- O `ROS_DOMAIN_ID` precisa ser o mesmo no robô e no PC.

Pergunte à equipe do INF qual dos dois modos o robô usa. **Não mude a configuração de rede do robô sem autorização.**

```bash
ros2 topic list                          # deve listar /battery_state, /dock_status, /scan
ros2 topic echo /battery_state --once
ros2 topic echo /dock_status --once
ros2 topic hz /battery_state             # deixe rodar 1 minuto e anote
```

Se o `ros2 topic hz` disser que o tópico não é publicado, tente com `--qos-profile sensor_data` (esses tópicos usam QoS de sensor; foi o que vimos no simulador, em `progresso/testes.md`).

**Feito quando:** os três tópicos respondem no PC. **Anote** a frequência do `/battery_state` e o maior intervalo entre mensagens: o campo `tempos.bateria_perdida_s` da configuração deve ser pelo menos 3 vezes esse intervalo (PAT-18).

### 2. Teleop: o robô anda e para pelo comando

Página: [Driving your TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/driving.html).

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

O manual diz que, no Jazzy, o parâmetro `stamped` precisa ser ligado à mão. Tire o robô da doca pela etapa 3 antes de andar: a documentação da Create 3 desaconselha comandar movimento com o robô encaixado.

**Feito quando:** o robô anda para frente, gira e para quando você solta a tecla.

### 3. Dock e undock à mão

Página: [Docking, Create 3](https://iroboteducation.github.io/create3_docs/api/docking/).

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
ros2 topic echo /dock_status --once      # is_docked: false
ros2 action send_goal /dock irobot_create_msgs/action/Dock "{}"
ros2 topic echo /dock_status --once      # is_docked: true
```

No undock, o robô recua e gira 180 graus. O dock falha se o robô estiver longe demais da doca.

**Feito quando:** as duas ações terminam com sucesso e o `/dock_status` muda nos dois sentidos. **Anote** quanto tempo o `is_docked: true` demora a aparecer depois do dock: é o que decide a hipótese H2 no robô real e o valor de `confirma_dock_s`.

### 4. Fazer o mapa (SLAM), começando com o robô na doca

Página: [Generating a map](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/generate_map.html).

Comece com o robô **encaixado na doca** (hipótese H3): assim a doca fica perto da origem do mapa, e a pose inicial fica fácil.

```bash
ros2 launch turtlebot4_navigation slam.launch.py
ros2 launch turtlebot4_viz view_navigation.launch.py     # RViz, em outro terminal
```

Faça o undock (etapa 3), dirija devagar pelo laboratório com o teleop (etapa 2) até o mapa fechar, e salve:

```bash
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "name: {data: 'lab'}"
```

O nome do launch do RViz (`view_navigation.launch.py`) e o formato exato do comando de salvar devem ser conferidos na página: escrevi de memória, e a busca só confirmou o serviço `/slam_toolbox/save_map`.

**Feito quando:** existem `lab.yaml` e `lab.pgm`, e a imagem mostra as paredes do laboratório sem "fantasmas" (paredes duplicadas). Guarde os dois arquivos em `progresso/evidencias/`.

Esse par de arquivos é o formato que o nosso `validar_pontos` lê. Qualquer mapa nosso, feito por SLAM ou por outro método, serve, desde que saia nesse formato (`.yaml` com `image`, `resolution` e `origin`, e a imagem em `.pgm`).

### 5. Localização e Nav2 em velocidade reduzida

Página: [Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html).

```bash
ros2 launch turtlebot4_navigation localization.launch.py map:=lab.yaml
ros2 launch turtlebot4_navigation nav2.launch.py params_file:=<caminho>/nav2_inf_devagar.yaml
ros2 launch turtlebot4_viz view_navigation.launch.py
```

No RViz, marque a pose inicial ("2D Pose Estimate") e mande um destino próximo ("Nav2 Goal"), com a pessoa de segurança ao lado.

O arquivo `nav2_inf_devagar.yaml` é uma cópia do `nav2.yaml` oficial com a velocidade máxima em 0,15 m/s (INF-02). **Pendente:** ele é gerado a partir do arquivo da imagem Docker e ainda não existe (ver `docs/registro-de-mudancas.md`).

**Feito quando:** um destino marcado no RViz chega, e o robô não passa de 0,15 m/s.

### 6. Escolher os pontos e validar

No RViz, use a ferramenta "Publish Point" e leia as coordenadas:

```bash
ros2 topic echo /clicked_point
```

Copie `config/inf_lab.yaml` para um arquivo novo e preencha: `mapa`, `pose_inicial` (onde o robô fica quando encaixado), `aproximacao_doca` (de frente para a doca, a cerca de 0,5 a 1 m, a confirmar) e `pontos`. Preencha também `tempos.bateria_perdida_s` com o valor da etapa 1. Depois:

```bash
validar_pontos <caminho>/inf_lab_preenchido.yaml
```

O `validar_pontos` não usa ROS nem robô. Ele recusa pose fora do mapa, em célula ocupada, em área não mapeada ou a menos de 0,25 m de um obstáculo.

**Feito quando:** o comando diz `APROVADA`. Este é o item 1 do protocolo: sem ele, nenhum movimento autônomo.

### 7. Patrulha com 1 ponto

Deixe só 1 ponto na lista `pontos`, perto da doca, e rode de novo o `validar_pontos`. Com o robô **na doca**, a localização e o Nav2 da etapa 5 rodando:

```bash
ros2 launch patrulha_tb4 patrulha.launch.py config:=<caminho>/inf_lab_preenchido.yaml
```

O nó faz o undock, vai ao ponto e repete. Pare com `Ctrl+C` depois de 2 ou 3 idas. O log fica em `~/.ros/patrulha/`.

**Feito quando:** o log tem `undock_ok` e pelo menos 2 `destino_ok`, e o `Ctrl+C` gravou `encerrado` e `resumo`.

Se o nó sair sozinho, o código de saída diz o motivo (tabela no `DEFINE.md`): 6 é "começou fora da doca", 3 é "sem bateria", 8 é "servidor de ação indisponível".

### 8. Patrulha completa, devagar

Volte a lista completa de pontos, rode o `validar_pontos` e a patrulha.

**Feito quando:** 1 volta completa sem intervenção (todos os pontos com `destino_ok`).

### 9. Ciclo de recarga com limites temporários

A bateria real cai devagar (hipótese H5). Para ver a volta à doca em minutos, troque na configuração:

```yaml
  bateria:
    modo: relativo
```

Com isso, os limites passam a ser calculados da primeira leitura: a patrulha volta à doca quando a carga cair 1 ponto percentual e sai de novo quando recuperar meio ponto (PAT-21). O log mostra os limites usados no evento `limites_bateria`.

Se a leitura da bateria oscilar e o robô voltar à doca cedo demais, aumente `delta_baixa` e `delta_critica` (mantendo `delta_alta < delta_baixa < delta_critica`).

**Feito quando:** o log tem, nesta ordem, `bateria_baixa`, `dock_ok`, `carga_completa`, `undock_ok` e `destino_ok`.

### 10. Aceite, com gravação

Com os números combinados com o coordenador (padrão proposto: 2 voltas e 1 ciclo de recarga, INF-03). Grave um rosbag durante toda a execução (INF-04):

```bash
ros2 bag record -o aceite_$(date +%F_%H-%M) /battery_state /dock_status /scan /odom /tf /tf_static /amcl_pose /cmd_vel /plan
```

Página: [Recording and playing back data](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html). A lista de tópicos é uma proposta: confira os nomes com `ros2 topic list` no dia.

A execução é **invalidada** por qualquer comando manual, reposicionamento à mão ou parada de segurança.

**Feito quando:** o log JSONL e o rosbag estão em `progresso/evidencias/`, com o registro de que o protocolo foi cumprido (quem estava ao lado, a velocidade usada e o resultado do `validar_pontos`).

## Folha de anotações do dia

| O que anotar | Etapa | Valor |
|---|---|---|
| Modo de rede (Simple Discovery ou Discovery Server) e `ROS_DOMAIN_ID` | 1 | |
| Frequência do `/battery_state` e maior intervalo | 1 | |
| Tempo até `is_docked: true` depois do dock | 3 | |
| Carga da bateria no início e no fim | 1 e 10 | |
| Pose da doca no mapa | 4 e 6 | |
| Tempo de 1 volta | 8 | |
| Quem ficou ao lado do robô | todas | |

## O que falta decidir ou preparar

| Item | Situação |
|---|---|
| Como o notebook fala com o robô | O container atual (`treino_leve.sh`, `ros.sh`) usa a rede isolada do Docker. Para o robô real, ele precisaria da rede do computador (`--network host`) e da configuração de discovery do laboratório. **Não foi feito nem testado** |
| Patrulha no PC ou no Raspberry Pi | Decisão aberta (DESIGN, seção 7). Este kit supõe o PC |
| `nav2_inf_devagar.yaml` | A gerar a partir do `nav2.yaml` da imagem |
| Tela do robô com ruído (foto `erro_tela.jpeg`, de 2026-11-12) | Não investigado. Não faz parte da patrulha, mas vale perguntar à equipe do INF antes de usar esse robô |

## Efeito prático

No laboratório, o trabalho é seguir a lista e preencher um arquivo. Se uma etapa falhar, você sabe em qual camada está o problema (rede, base, mapa, Nav2 ou a nossa patrulha) sem ter de adivinhar. E os números anotados nas etapas 1 e 3 voltam para casa: eles ajustam o `bateria_perdida_s` e o `confirma_dock_s`, e decidem as hipóteses H2 e H5 da spec.

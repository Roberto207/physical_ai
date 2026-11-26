# BRAINSTORM: task 2, busca colaborativa com três TurtleBots 4

**Status:** fase 2a do `/sdd` (divergente). Mapeia o problema e as opções, sem escolher. A escolha é da fase Define.
**Data:** 2026-11-26
**Enunciado:** `images/task_multi_robos.jpeg` (fora do git, como toda a pasta `images/`)

## 1. O que o desafio pede

**Formato das rodadas**

- Até 4 objetos por rodada.
- Os objetos são pedidos em linguagem natural e ficam em posições desconhecidas.
- Rodadas de 10 minutos, da saída das docas até os três robôs reencaixados.

**Etapas:** saída das docas → busca distribuída → detecção e aviso → confirmação por outro robô → retorno às docas.

| # | Requisito | O que significa para nós |
|---|---|---|
| 1 | Mapeamento e localização | Um mapa único, com os três robôs no mesmo referencial |
| 2 | Percepção visual | Identificar os objetos e estimar a posição deles no mapa (câmera OAK-D) |
| 3 | Arquitetura multiagente | Um coordenador e um agente por robô, todos com a mesma LLM central |
| 4 | Reasoning | Distribuir a busca, revisar o plano e decidir quando retornar |
| 5 | Memória e comunicação | Áreas visitadas e estado de cada objeto (não encontrado, localizado ou concluído) |
| 6 | Execução | Metas válidas para o Nav2, da saída ao reencaixe |
| 7 | Confirmação cruzada | Outro robô verifica o alvo enquanto a busca continua |
| 8 | Supervisão | Mapa, objetos, tempo restante e decisões numa só tela |

**Pontuação**

- Um objeto só conta como concluído quando um robô o detecta e outro o confirma, dentro da tolerância.
- Ganha quem concluir mais objetos. No empate, ganha o menor tempo.
- Os três robôs precisam estar nas docas no prazo.

**Entregas**

- Código, configuração e instruções.
- Diagrama dos agentes.
- Demonstração completa.
- Registro de observações, decisões e tempos.
- Relatório.

## 2. Onde estamos (depois da reformulação)

| Já temos | Falta |
|---|---|
| Nav2, localização e patrulha por namespace (`scripts/env.sh`, `-r __ns:=`) | Mais de um robô ao mesmo tempo no PC |
| LLM local (Ollama) que transforma pedido em ação validada | Coordenador, um agente por robô e memória compartilhada |
| Mapa `mapa_lab_novo` (cerca de 60% não mapeado) | Mapa completo da área da prova e uma doca medida por robô |
| `robot1` e `robot3` configurados | Terceiro robô, percepção e supervisão |

**O bloqueio de hoje:** o PC fala com um robô por vez. Os três robôs usam a mesma sub-rede interna 192.168.186.0/24 (USB da Create 3) e a 192.168.185.0/24, e a rota do PC para cada uma só pode apontar para um robô. A rota foi exigida porque, sem ela, a descoberta do DDS não fechava (medido em 2026-11-16).

## 3. O que a pesquisa achou

### Rede

A doc oficial (`turtlebot4-user-manual/setup/discovery_server.html`) prevê vários robôs:

- cada robô tem o próprio Discovery Server, com id único e namespace único;
- o PC é cliente de todos, com `ROS_DISCOVERY_SERVER="ip1:11811;ip2:11811;..."`;
- a página `setup/networking.html` recomenda Discovery Server para "1+ robots running complex functionality such as navigation".

### H1: talvez não precise de rota

A mesma página diz que, no Humble com o `create3_republisher`, "this route is no longer necessary/used and can be removed". O repositório do colega roda sem nenhuma rota.

Se isso valer no nosso firmware, o bloqueio da seção 2 some.

**Teste (só leitura, no PC do lab):**

1. Remover temporariamente as duas rotas.
2. Rodar `scripts/checar.sh` e conferir se `odom`, `battery_state` e `dock_status` chegam.
3. Com os dados chegando, rodar `ros2 topic hz <ns>/odom`.

### SSH

A ideia inicial era rodar tudo no PC e mandar ao robô por SSH. A doc não usa SSH como canal de controle. O SSH serve para administrar o robô (`turtlebot4-setup`, reiniciar o serviço `turtlebot4`). Dados e metas vão por DDS.

O desenho provável é este:

- os processos rodam no PC, um conjunto por namespace;
- a conversa com os robôs é por DDS;
- o SSH fica só para manutenção.

### Simulação

Doc oficial `tutorials/multiple_robots.html`:

```bash
ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py namespace:=/robot1 nav2:=true localization:=true
ros2 launch turtlebot4_ignition_bringup turtlebot4_spawn.launch.py namespace:=/robot2 x:=0.0 y:=1.0 nav2:=true localization:=true
```

A doc avisa que "not all functionality is currently fully supported in multi-robot simulation".

### Problemas conhecidos

- **turtlebot4 #410:** no segundo robô simulado, o AMCL não acha `amcl_pose` e o dock falha.
- **navigation2 #4350:** `waitUntilNav2Active()` trava com namespace. O nosso `robo.esperar_servidores` já não usa essa função.
- **Carga:** com os serviços do PC no ar, a Create 3 do `robot3` chegou a 100% de processador (`docs/tarefas/2026-11-25-llm-robot3-correcoes.md`). Com três robôs, o número de assinantes por robô importa.

### Coordenação com LLM (referências)

| Referência | O que é | Onde |
|---|---|---|
| ROSA (NASA JPL) | Agente LLM sobre ROS | arXiv 2410.06472 |
| CoMuRoS | LLM gerente que distribui subtarefas a agentes por robô | arXiv 2511.22354 |
| RobotFleet | Planejamento central e agentes por robô | arXiv 2510.10379 |
| Survey de LLM em multi-robô | Panorama da área | arXiv 2502.03814 |

## 4. Arquiteturas candidatas

| | Onde roda | A favor | Contra |
|---|---|---|---|
| A | Tudo no PC (Nav2, localização, agentes e LLM), por DDS, um namespace por robô | É o que a doc descreve; é o que já fazemos para um robô | CPU do PC, tráfego no Wi-Fi, carga na Create 3 |
| B | Nav2 em cada Raspberry Pi; coordenador e LLM no PC | Menos tráfego de Nav2 pelo Wi-Fi | RPi4 com Nav2 tem relatos de carga alta; a doc não recomenda |
| C | Processos dos robôs lançados por SSH | Isola cada robô | Sem padrão oficial; gerenciar processos fora do ROS |
| D | Híbrida: drivers no Pi, Nav2 por namespace em contêineres no PC, coordenador à parte | Reaproveita os `scripts/` | Os mesmos riscos da A |

## 5. Hipóteses e riscos para a fase Define

- **H1:** o PC sem as rotas internas recebe os dados dos três robôs (teste acima).
- **H2:** o PC do lab aguenta três pilhas de localização e Nav2 (medir CPU e memória com dois robôs primeiro).
- **H3:** o `TurtleBot4Navigator` com `-r __ns:=` funciona para dois robôs no mesmo PC. Cada robô roda num processo, como hoje.
- **Relógio:** chrony dos Pi apontando para o PC do lab (sugestão da mantenedora na #410).
- **Colisão:** cada Nav2 vê os outros robôs só pelo laser. Ver se basta ou se o coordenador precisa separar as áreas.
- **Mapa:** completar o `mapa_lab_novo` ou fazer um novo da área da prova, e medir a doca de cada robô.

## 6. Perguntas em aberto

- Onde será a prova (o laboratório atual?) e quais são os objetos?
- A "LLM central" pode ser o Ollama local, ou a prova exige outro modelo?
- O terceiro robô já está disponível? Qual é o namespace dele?
- Qual é a tolerância de posição da confirmação cruzada?

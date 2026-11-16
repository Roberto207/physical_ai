# Semana 3: Nav2 e o patrol_loop (8 horas)

## O que é esta semana

Entender o que o Nav2 faz por você, rodar o exemplo oficial de patrulha e explicá-lo linha a linha. Esta semana é mais de **ler código** do que de escrever.

## Por que

Sua missão 1 é melhorar esse exemplo. Quem não entende o original reescreve os mesmos defeitos. E o `patrol_loop` já mostra quase tudo: bateria, base, navegação.

## Como um robô chega a um lugar

O equivalente de uma viagem de carro:

| Etapa | Pergunta | Nome técnico | Viagem de carro |
|---|---|---|---|
| Mapa | Como é o lugar? | Mapa pronto, feito antes com SLAM | O mapa da cidade |
| Localização | Onde estou nele? | AMCL, compara lidar com mapa | O ponto azul do GPS |
| Rota | Por onde vou? | Planejador global | O GPS traçando a rota |
| Direção | Como sigo agora? | Controlador local | Você no volante, desviando |
| Plano B | E se travar? | Behavior tree e recuperações | Dar ré e tentar outro caminho |

O **Nav2** faz tudo isso. Você entrega um destino pela action `navigate_to_pose` e recebe progresso e resultado.

**Pose inicial:** o manual avisa que a localização exige uma pose inicial antes de navegar. Sem isso, o robô não sabe onde está no mapa. No código, é `setInitialPose`.

## As camadas de código

| Camada | O que oferece | Quem usa |
|---|---|---|
| Nav2 | A action `navigate_to_pose` | Todo mundo |
| `BasicNavigator` (Nav2 Simple Commander) | `goToPose`, `isTaskComplete`, `getFeedback`, `cancelTask`, `getResult` | Python |
| `TurtleBot4Navigator` | Herda tudo acima e soma `dock`, `undock`, `getDockedStatus`, `startToPose`, `getPoseStamped` | Suas missões |

A diferença que vai importar na semana 4:

| Método | Comportamento | Comparação |
|---|---|---|
| `startToPose` | **Trava** o programa até chegar ou falhar | Ligar e ficar na linha até atender |
| `goToPose` | Dispara e devolve o controle. Você consulta com `isTaskComplete` | Mandar mensagem e continuar trabalhando |

## O que estudar (cerca de 3 horas)

| Ordem | Material | Foco |
|---|---|---|
| 1 | [TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) | As seções Navigate to Pose, Follow Waypoints e Patrol Loop |
| 2 | [Navegação no manual](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html) | Pose inicial e destino |
| 3 | [Primeiros passos do Nav2](https://docs.nav2.org/rolling/getting_started/) | Só a visão geral. Não tente entender os parâmetros |
| 4 | [Simple Commander](https://docs.nav2.org/rolling/configuration_and_development/simple_commander_api/simple_commander_api/) | A lista de métodos |

## Praticar (cerca de 4 horas)

### Parte 1: rodar

```bash
infra/docker/treino_leve.sh iniciar --rviz --patrulha
infra/docker/treino_leve.sh logs        # espere uns 30 s
infra/docker/treino_leve.sh terminal    # em outra aba
```

No terminal, use o que aprendeu na semana 1:

```bash
ros2 node list
ros2 action list                        # ache /navigate_to_pose, /dock e /undock
ros2 topic echo /battery_state --field percentage
ros2 topic hz /cmd_vel
```

**Espere falhas.** Neste simulador a navegação está lenta, e pode dar `Goal failed`. É um problema conhecido, ver `praticar.md`. Não tente consertar: o objetivo aqui é ver o fluxo do programa.

Depois de ver o fluxo, deixe pelo menos uma execução com bateria que descarrega depressa:

```bash
infra/docker/treino_leve.sh parar
BATERIA_INICIAL=0.35 DESCARGA=0.005 infra/docker/treino_leve.sh iniciar --patrulha
```

### Parte 2: ler

Abra `/opt/tb4_ws/src/turtlebot4_tutorials/turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py` e explique por escrito cada bloco:

1. `BatteryMonitor`: por que é um nó separado, numa thread?
2. Início: por que garante estar na base **antes** de definir a pose inicial?
3. Por que os limites são três (0,95, 0,2 e 0,1)?
4. O `while True`: desenhe o fluxograma com os três caminhos da bateria.

### Parte 3: achar os defeitos

Encontrei três. Tente achar sozinho antes de ler a resposta, no fim deste arquivo.

## Pronto quando

Você desenha o fluxograma do `patrol_loop` de cabeça, e responde: em que momento ele olha a bateria?

## Se travar

- `logs` dá erro: o arquivo só existe depois de uns 20 s, ou a opção `--patrulha` faltou.
- O RViz não aparece: confira `echo $DISPLAY`. Não confirmei a janela do RViz funcionando, só que o processo iniciou.
- Falta memória: feche o navegador e tente sem `--rviz`.

## Resposta: os três defeitos

1. **Bateria sem valor inicial:** `self.battery_percent` só passa a existir na primeira mensagem. Se o laço chegar antes, o programa quebra com `AttributeError`.
2. **Só olha a bateria entre destinos:** `startToPose` trava até chegar. No meu teste, com a descarga acelerada de propósito, a bateria foi de 90% a 0% num único trecho, sem reação.
3. **Ignora o resultado:** se um destino falha, ele só registra no log e passa para o próximo, sem contar falhas nem avisar.

Consertar os três é o coração da semana 4.

# O `patrol_loop`: como funciona e o que vimos

## Resposta direta

O `patrol_loop` é o exemplo oficial de patrulha do pacote `turtlebot4_python_tutorials`. O robô percorre pontos em loop e, quando a bateria fica baixa, volta à base para carregar. Em 9/nov ele rodou inteiro no simulador leve, e vimos ao vivo um dos três defeitos que tínhamos achado lendo o código.

## A cena do dia a dia

Um **vigia de galpão** que faz a ronda por pontos fixos. Antes de cada ponto ele confere o quanto está cansado. Se estiver cansado, vai à sala de descanso (a base) e só volta depois de recuperado. O defeito é que ele só se confere **entre um ponto e outro**: se o trecho for longo, pode cair exausto no corredor.

## Fluxo do programa

| Passo | O que faz | Nome no código/log |
|---|---|---|
| 1 | Garante que está na base e define a pose inicial | `setInitialPose` |
| 2 | Espera o Nav2 ficar pronto | `Nav2 is ready for use!` |
| 3 | Sai da base | `Undocking...` |
| 4 | Lê a bateria e vai ao próximo destino (trava até chegar ou falhar) | `startToPose` |
| 5 | Se a bateria está baixa (menos de 20%), vai à base | `Docking for charge` |
| 6 | Faz o dock e espera carregar até 95% | `Docking...`, `Charging...` |
| 7 | Se a bateria está crítica (menos de 10%), encerra | |
| 8 | Volta ao passo 3 | |

Limites: 0,95 (carregado), 0,20 (baixa) e 0,10 (crítica).

## Camadas de código

| Camada | O que oferece |
|---|---|
| Nav2 | A action `navigate_to_pose` |
| `BasicNavigator` | `goToPose`, `isTaskComplete`, `getFeedback`, `cancelTask`, `getResult` |
| `TurtleBot4Navigator` | Tudo acima mais `dock`, `undock`, `getDockedStatus`, `startToPose` |

`startToPose` **trava** o programa até chegar ou falhar. `goToPose` dispara e devolve o controle, e você consulta com `isTaskComplete`. Essa diferença é a raiz do defeito 2.

## Os três defeitos (achados lendo o código em 5/nov)

| # | Defeito | Consequência |
|---|---|---|
| 1 | Bateria sem valor inicial: `battery_percent` só existe depois da primeira mensagem | `AttributeError` se o laço chegar antes |
| 2 | Só olha a bateria entre destinos | Num trecho longo, a bateria zera sem reação |
| 3 | Ignora o resultado do destino | Se um destino falha, só vai ao próximo, sem contar falhas |

## Execução de 9/nov (simulador leve)

Condições: bateria inicial de 30%, descarga de 0,001 por segundo, carga de 0,05 por segundo, mapa `warehouse`. De onde vem cada parte desse ambiente (o que é oficial e o que é nosso): ver `origem-das-pecas.md`. Log completo em `evidencias/patrol_loop-leve-2026-11-09.log`.

| Momento | Evento | Bateria |
|---|---|---|
| Início | Undock ok | 85% (a base falsa carregou enquanto o sistema subia) |
| Trecho 1 | Vai a `(-5, 1)` e chega | 85% a 64% |
| Trecho 2 | Vai a `(-5, -23)` e chega | 64% a 42% |
| Trecho 3 | Vai a `(9, -23)` e chega | 42% a 19,9% |
| Decisão | `Docking for charge`, vai a `(-1, 1)` | 19,9% |
| Volta | Trecho de cerca de 255 s | cai a 0% no caminho |
| Fim | `Dock succeeded` e depois `ERROR Robot failed to dock`; o programa para | |

### O que isso mostra

1. **O defeito 2 apareceu ao vivo:** a bateria foi de 19,9% a 0% no trecho de volta e o programa só "viu" ao chegar. No robô real, ele pararia no meio do corredor.
2. **O caminho de docking rodou pela primeira vez.**
3. **O erro final provavelmente é da base falsa.** O código (linha 115 de `patrol_loop.py`) checa `getDockedStatus()` logo depois do `dock()` e, se for falso, loga `Robot failed to dock` e sai do laço. O `/dock_status` depois mostrava `is_docked: true`. Hipótese: o status chegou um instante depois da checagem. **Não confirmado**, e no robô real pode ser diferente. Em 2026-11-10 li o `getDockedStatus()`: ele lê o último status guardado, o que reforça a hipótese (ver "O erro de dock" abaixo).
4. **A falha de navegação de 5/nov não se repetiu**, e a causa continua desconhecida.

### Limites do teste

- Base, bateria e AMCL são falsos (escritos por nós). Nada aqui prova o comportamento do robô real.
- A descarga foi acelerada de propósito.
- Uma única execução.

## Estado da primeira entrega: parcial (2026-11-09)

Esta é a primeira entrega da equipe. O que o exemplo oficial promete, e o que foi comprovado no simulador leve:

| Requisito | Situação | Evidência |
|---|---|---|
| Sair da base | Cumprido | `Undock succeeded` |
| Dirigir por pontos | Cumprido | Chegou a `(-5, 1)`, `(-5, -23)` e `(9, -23)` |
| Monitorar a bateria | Cumprido, com ressalva | Lê só entre destinos; no trecho de volta foi a 0% sem reação (defeito 2) |
| Voltar à base com bateria baixa | Cumprido | `Docking for charge` aos 19,9% |
| Chegar à base e encaixar | **Parcial** | A action devolveu `Dock succeeded`, mas o programa logou `Robot failed to dock` |
| Carregar e retomar a patrulha | **Não cumprido** | O programa parou antes de `Charging...` |
| Repetir o loop | **Não cumprido** | Nenhum ciclo completo foi observado |
| Nossa patrulha melhorada (missão 1) | **Não começada** | Só a leitura do código e os testes em Python puro |

**Gates de entrega:** não há registro deles em nenhum arquivo do projeto (busquei por "gate" e "portão"). Preencher aqui quando o Roberto passar a lista, e conferir cada gate contra a tabela acima.

Limite de tudo isso: o simulador leve tem base, bateria e AMCL falsos. Cumprir um requisito aqui prova a lógica do programa, não o comportamento no robô real.

## A bateria zerou no trecho de volta: causa

**Resposta: é um defeito do `patrol_loop` (do sistema), e não do simulador leve.** O simulador só forneceu o cenário.

| Fato | Evidência |
|---|---|
| A bateria caiu de forma regular, a 0,1% por segundo, como configurado | 85% a 64,2% em 207 s; 64,2% a 42% em 222 s; 42% a 19,9% em 221 s (log) |
| O programa leu a bateria **só nos três momentos em que um destino terminou** | Linhas `Battery is at ...` no log, uma por destino |
| O trecho de volta durou cerca de 255 s | Entre `Docking for charge` e `Docking...` |
| Em 255 s a 0,1% por segundo, a bateria cai 25,5 pontos, e 19,9% acaba em cerca de 199 s | Conta: a bateria chegou a 0% cerca de 56 s antes de chegar à base. A base falsa mostrou `encaixado com 0%` |

Motivo: o `patrol_loop` usa `startToPose`, que **trava** o programa até o destino terminar. Enquanto ele espera, ninguém olha a bateria. Esse é o defeito 2, e ele existiria no robô real.

O que é do nosso ambiente (e não do exemplo):

1. **A velocidade da descarga** (0,1% por segundo) foi escolhida por nós para ver a reação em poucos minutos. No robô real a descarga é muito mais lenta, e o problema só aparece em trechos longos com bateria já baixa.
2. **A bateria começou em 85%, e não em 30%**: a base falsa carrega a 5% por segundo enquanto o robô está nela, e o sistema levou cerca de 20 s para subir.
3. A bateria é **falsa**: ela segue exatamente a fórmula que escrevemos. Nada diz como seria a bateria do robô real.

Por isso o defeito é real, mas a gravidade no robô real é outra pergunta, e só um teste lá responde.

## O erro de dock: tudo o que há registrado

**O que o log mostra** (`evidencias/patrol_loop-leve-2026-11-09.log`):

```
[1794263262.840] Docking...
[1794263262.865] Dock succeeded
[1794263262.865] ERROR Robot failed to dock
```

O erro vem **0,6 milissegundo** depois do sucesso (os dois estão em `.865`). A base falsa registrou `dock falso: encaixado com 0%` em `.845`.

**O que o código do `patrol_loop` faz** (linhas 113 a 117 de `patrol_loop.py`):

```python
navigator.dock()
if not navigator.getDockedStatus():
    navigator.error('Robot failed to dock')
    break
```

Ou seja, ele confia no `getDockedStatus()`. Se vier falso, escreve o erro e **sai do laço**, e o programa termina.

**O que o código da nossa base falsa faz** (`infra/tools/fake_tb4_base.py`):

- A action `/dock` marca `self.docked = True` e devolve sucesso **na hora**.
- O tópico `/dock_status` só é publicado dentro do `tick()`, que roda **uma vez por segundo**.
- Então, logo depois do dock, o último `/dock_status` publicado ainda dizia "não está na base" (era o do `undock`), por até 1 s.

**Depois do erro:** consultando o tópico, `is_docked: true` e `dock_visible: true`.

**Conclusão provável (hipótese forte, não comprovada):** o `getDockedStatus()` leu um valor antigo. O intervalo de 0,6 ms é curto demais para ele ter esperado uma nova mensagem, o que combina com leitura do valor guardado. A causa estaria na **nossa base falsa**, que atualiza o status com atraso de até 1 s, e não no `patrol_loop`.

**O que NÃO foi verificado:**

1. ~~Não li o código do `getDockedStatus()`~~ Lido em 2026-11-10 (`turtlebot4_navigation/turtlebot4_navigator.py`, linha 162): ele faz **um** `spin_once` de 0,1 s e devolve o último `is_docked` guardado. Isso combina com a hipótese: se nenhuma mensagem nova chegou nesses 0,1 s, ele devolve o "não está na base" do undock. A hipótese ficou mais forte, mas continua sem o teste que decide.
2. Não repeti a execução depois de corrigir a base falsa.
3. No robô real, a base de carga do Create 3 se comporta de outro jeito, e o erro pode não existir lá.

**Teste que decide:** fazer a base falsa publicar `/dock_status` imediatamente quando `do_dock` roda (em vez de esperar o próximo `tick()`) e rodar a patrulha de novo. Se aparecer `Charging...`, a hipótese está confirmada.

**Resultado do teste que decide (2026-11-12): hipótese confirmada.** A base falsa passou a publicar o `/dock_status` dentro do `do_dock` e do `do_undock`. O `patrol_loop` oficial, sem nenhuma alteração, foi rodado de novo:

```
[1794536349.332] Docking...
[1794536349.336] Dock succeeded
[1794536349.337] Charging...
```

Não houve `Robot failed to dock`. O erro de 9/nov era da nossa base falsa. Log em `evidencias/patrol_loop-leve-2026-11-12-h2.log`. Continua valendo o item 3 acima: no robô real, o comportamento da doca precisa ser medido.

## Pronto para o robô do INF? Medição (2026-11-10)

**Resposta direta: não.** Se rodássemos hoje o `patrol_loop` no TurtleBot 4 do INF, ele tentaria ir a pontos do galpão de mentira (`warehouse`), que não existe no laboratório. A spec do caminho até lá está em `../specs/patrol-inf/`.

Medição feita só lendo arquivos e o código dentro da imagem `physical-ai:jazzy`. Nada foi rodado no robô.

### O que vai para o robô e o que fica

| Peça | Vai para o robô? |
|---|---|
| `patrol_loop` (oficial) ou a nossa patrulha melhorada | Sim: roda no PC, pela rede, ou no Raspberry Pi do robô (**decisão aberta**) |
| `infra/tools/fake_tb4_base.py` (bateria, doca e AMCL falsos) | Não: o robô tem bateria, doca e AMCL de verdade |
| `nav2_loopback_sim` (simulador leve) e `infra/docker/treino_leve.sh` | Não: o robô se move de verdade |
| Mapa `warehouse.yaml` | Não: o laboratório precisa de um mapa próprio, feito com SLAM |
| `workspace/exemplos/decisao_patrulha.py` | Ainda não: é uma função pura, e nenhum nó ROS a usa |
| `workspace/meu_ws/src/` | Está **vazio**: o nosso pacote ainda não existe |

### As 9 áreas

| Área | Situação | O que falta |
|---|---|---|
| Lógica da patrulha (simulada) | Parcial | Fechar o ciclo de recarga no leve (`Charging...` nunca apareceu) |
| Nosso código (missão 1) | Não começado | Pacote com a patrulha melhorada, com pontos e pose num YAML |
| Mapa do laboratório | Não existe | SLAM no INF |
| Pontos de patrulha do INF | Não existem | Escolher no mapa novo |
| Rede entre o robô e o PC | Desconhecida | `ROS_DOMAIN_ID`, middleware (a imagem só tem `rmw_fastrtps_cpp`) e discovery |
| Modelo do robô | Desconhecido | Standard ou Lite (o URDF usado no leve é o Standard) |
| Acesso ao robô | Sem acesso | Como reservar no INF |
| Segurança no teste | Não planejada | Velocidade baixa, alguém ao lado, área livre, como parar |
| Testes no robô | Zero | Teleop, dock, um destino, e depois a patrulha |

Uma área está parcial e 8 não foram começadas ou são desconhecidas. Quatro delas (mapa, pontos, rede e testes) só podem ser feitas no INF.

### O que impede o `patrol_loop` oficial de funcionar no INF

| # | Problema | Linhas de `patrol_loop.py` | Efeito no robô |
|---|---|---|---|
| 1 | Pontos fixos do `warehouse`: `(-5, 1)`, `(-5, -23)`, `(9, -23)` e `(10, 2)` | 92 a 95 | Destinos que não existem no laboratório |
| 2 | Pose inicial fixa em `(0, 0)` virado para o norte, e a aproximação da doca em `(-1, 1)` | 81 e 111 | Só serve se o mapa tiver a doca na origem. Caso contrário, o AMCL começa perdido |
| 3 | Defeito 1: `battery_monitor.battery_percent` só existe depois da primeira mensagem | 99 | Quebra se a bateria demorar a chegar pela rede |
| 4 | Defeito 2: bateria só lida entre destinos (`startToPose` trava) | 111 e 138 | Um trecho longo passa do limite sem reação |
| 5 | Defeito 3: ignora quando um destino falha | 138 | Repete pontos inalcançáveis sem avisar |
| 6 | Bateria crítica só encerra o programa | 105 a 107 | O robô para onde estiver, longe da doca |

### Fatos novos (código lido em 2026-11-10)

| Fato | Onde | Consequência |
|---|---|---|
| `isDockComplete()` e `isUndockComplete()` devolvem `True` **também quando a ação falha**. Só escrevem no log, e com um atributo errado (`self.status`) | `turtlebot4_navigator.py`, logo depois do `dock()` | O `dock()` volta "normal" mesmo depois de falhar. Nosso código precisa checar o resultado da ação e depois o `/dock_status` |
| `waitUntilNav2Active()` espera o nó `amcl` e uma `/amcl_pose` | `nav2_simple_commander/robot_navigator.py`, linhas 495 a 503 e 795 | É por isso que a base falsa finge o AMCL no leve. No robô real, o AMCL de verdade responde |
| O simulador leve publica a posição perfeita (`map→odom` e `odom→base_link`) e um **`/scan` calculado contra o mapa** | `nav2_loopback_sim/loopback_simulator.py` (`publishTransforms`, `publishLaserScan`) | Há um lidar calculado sobre o mapa, sem física. A localização nunca erra, então o leve não testa um robô perdido |
| O leve usa por padrão os parâmetros do Nav2 do `nav2_bringup`, e não os do TurtleBot 4 (`turtlebot4_navigation/config/nav2.yaml`, velocidade máxima de 0,26 m/s) | `tb4_loopback_simulation.launch.py`, argumento `params_file` | O teste do leve não usa a configuração do robô real. Dá para trocar com `params_file:=` (a validar) |

### Os dois jeitos de rodar no robô (decisão aberta)

| Jeito | Vantagem | Cuidado |
|---|---|---|
| No PC, pela rede Wi-Fi | Não instala nada no robô e é fácil de editar | Depende do Wi-Fi durante a patrulha |
| No Raspberry Pi do robô (copiar e compilar com `colcon build`) | Não depende do Wi-Fi | Pouca memória, e atualizar dá mais trabalho |

## Pontos de partida para a missão 1

1. Consertar o defeito 2: olhar a bateria **durante** o trajeto, usando `goToPose` e `isTaskComplete` em vez de `startToPose`.
2. Dar valor inicial à bateria e esperar a primeira mensagem (defeito 1).
3. Tratar o resultado de cada destino (defeito 3), contando falhas.
4. Separar a decisão em função pura testável (`workspace/exemplos/decisao_patrulha.py`, já com testes).
5. Resolver o falso erro de dock: esperar `is_docked` por alguns segundos antes de desistir.

## Efeito prático

O defeito 2 é o mais fácil de demonstrar e o que mais importa no robô real. Se a reunião pedir "o que você vai melhorar primeiro", é esse.

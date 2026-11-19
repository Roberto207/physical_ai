# DESIGN: como construir e testar a patrulha para o robô do INF

**Status:** Aprovado em 2026-11-10 (portão da skill `/sdd`). Revisado em 2026-11-10, a pedido do Roberto: o Gazebo `maze` enxuto passa a ser o degrau L3 recomendado, a medição M-GZ fica pendente, o MVSim fica como plano B, e entram as seções 1.1 (quem responde a cada interface) e o modo de bateria relativo.
**Data:** 2026-11-10
**Base:** `BRAINSTORM.md` e `DEFINE.md` desta pasta

## Resposta direta

O design tem três partes:

1. Um pacote nosso, `patrulha_tb4`, em que **toda a decisão é uma função pura** e o nó ROS só lê sensores e executa.
2. A base falsa melhorada, que passa a provocar falhas de propósito.
3. Uma **escada de testes** que vai do mais barato (pytest, em segundos) ao robô do INF, e só sobe de degrau quando o anterior passa.

O que depende do laboratório (mapa, pontos e rede) fica num YAML e num kit de campo.

## A cena do dia a dia

Um **piloto de avião treina primeiro no simulador de mesa**, depois no simulador de cabine e só então voa. A lista de verificação é a mesma nos três. O que muda é o aeroporto, que vem num papel à parte (a configuração). Ele não aprende a decolar no dia do voo, só confere a lista.

## 1. O pacote `patrulha_tb4`

Local: `workspace/meu_ws/src/patrulha_tb4/`, do tipo `ament_python`. **Criar o pacote é um pedido separado**, depois da aprovação desta spec.

| Arquivo | Papel | Depende do ROS? | Requisitos |
|---|---|---|---|
| `patrulha_tb4/decisao.py` | Máquina de estados pura: recebe bateria, idade da última bateria, `na_base`, o resultado do último destino, a ação ativa e os contadores, e devolve a próxima ação e o evento. Evolução do exemplo `decisao_patrulha.py` (tag `jazzy-final`; reaproveitar `decidir()` e os testes de `test_decisao_patrulha.py`) | Não | PAT-03 a PAT-22 |
| `patrulha_tb4/config.py` | Carrega e confere o YAML (campos obrigatórios e limites em ordem: crítica < baixa < alta). No modo relativo, calcula os limites a partir de `b0` | Não | PAT-01, PAT-21, VAL-04 |
| `patrulha_tb4/pontos.py` | Valida as poses contra o mapa: lê o `.yaml` e o `.pgm` e converte (x, y) em célula com `origin` e `resolution`. Rejeita pose fora do mapa, ocupada ou desconhecida. Também tem um comando de linha `validar_pontos` | Não | VAL-01 a VAL-03 |
| `patrulha_tb4/registro.py` | Log JSONL e resumo final | Não | OBS-01 a OBS-03 |
| `patrulha_tb4/no_patrulha.py` | O nó: um `BatteryMonitor` numa thread (o mesmo padrão do `patrol_loop.py`, linhas 37 a 59) e o `TurtleBot4Navigator`. Laço de 1 s: `goToPose`, depois `isTaskComplete` e `getResult`, consulta `decidir()` e executa (`cancelTask`, `dock`, `undock`) | Sim | PAT, AMB e OBS |
| `config/leve_reduzido.yaml` | Pontos de 1,5 a 3 m de distância, num mapa pequeno (a escolher e validar: `depot` ou `maze`) | Não | TST-03 |
| `config/gazebo_maze.yaml` | Os mesmos pontos curtos do `maze`, com `ambiente: gazebo`, `bateria.modo: relativo` e `bateria_perdida_s: 30` | Não | TST-08 |
| `config/warehouse_original.yaml` (removido em 2026-11-19, P2 de `specs/enxugamento/SPEC.md`) | Os mesmos pontos do oficial, para comparar com o `patrol_loop` | Não | AMB-01 |
| `config/inf_lab.yaml` | Modelo **sem pontos**, para preencher no INF | Não | Protocolo, item 1 |
| `launch/patrulha.launch.py` | Argumentos `config`, `ambiente` e `use_sim_time`. Não abre o RViz | Sim | AMB-01 a AMB-03 |
| `test/` | pytest de `decisao`, `config`, `pontos` e `registro`, com `@pytest.mark.req("<ID>")` em cada teste. Também `test_lint_poses.py`, que procura `getPoseStamped` e poses com números literais fora de `test/`, e `checar_rastreio.py`, que falha se faltar um ID L0 | Não | TST-01, TST-02, TST-07 |
| `config/nav2_inf_devagar.yaml` | Cópia do `turtlebot4_navigation/config/nav2.yaml` com o `velocity_smoother.max_velocity` em x a 0,15 | Não | INF-02 |

### Como o nó confirma o dock (PAT-09 a PAT-11)

O `TurtleBot4Navigator.isDockComplete()` devolve `True` mesmo quando a ação falha. Por isso o nó **não confia só no `dock()`**. Ele:

1. guarda o resultado da ação (`dock_status` do navigator, igual a `GoalStatus.STATUS_SUCCEEDED`);
2. espera `is_docked: true` assinando `/dock_status` por até `T` s;
3. se uma das duas falhar, reaproxima e tenta de novo, até `K` vezes.

Assim não alteramos o pacote oficial.

### 1.1 O código não muda entre ambientes: quem responde a cada interface

O nó só conversa com **interfaces**: tópicos, ações e o Nav2. Ele não sabe, e não precisa saber, quem está do outro lado. É como uma tomada: o carregador do celular é o mesmo, seja a energia da rua ou de um gerador. A base falsa, a Create 3 simulada do Gazebo e a Create 3 real são três "geradores" diferentes atrás da mesma tomada.

| Interface que o nó usa | `leve` | `gazebo` | `real` (INF) |
|---|---|---|---|
| `/battery_state` | Base falsa (1 Hz, descarga acelerada) | `robot_state` da Create 3 simulada (0,1 Hz, descarga lenta e fixa no código) | Create 3 real (frequência a medir) |
| `/dock_status` | Base falsa | Create 3 simulada | Create 3 real |
| Ações `/dock` e `/undock` | Base falsa (só muda o estado, sem andar) | Nós da Create 3 simulada, com a doca `standard_dock` do mundo (o robô se move até encaixar) | Create 3 real |
| `navigate_to_pose` | Nav2 | Nav2 | Nav2 |
| Nó `amcl` e `/amcl_pose` (o `waitUntilNav2Active` espera) | Base falsa finge | AMCL real | AMCL real |
| Posição do robô | `loopback_simulator`, perfeita | AMCL com o lidar e a odometria simulados | AMCL com o lidar e a odometria reais |
| `/scan` | Calculado sobre o mapa | Lidar simulado (640 raios a 62 Hz) | RPLIDAR real |

O que muda de um ambiente para o outro fica **fora do código**:

- o arquivo de `config/` (ambiente, mapa, pontos, tempos e modo de bateria);
- os argumentos de launch (`use_sim_time`, AMB-02);
- o que se sobe ao lado do nó: a base falsa e o `loopback_simulator` no leve, o Gazebo no `gazebo`, nada no real.

Duas diferenças de comportamento entre os ambientes viraram **configuração**, para que o código siga único:

1. a frequência da bateria: daí o `bateria_perdida_s` por ambiente (PAT-18);
2. a descarga lenta no Gazebo e no robô real: daí o modo `relativo` (PAT-21).

Nada da base falsa ou do Gazebo vai para o robô.

### Esboço da configuração

```yaml
patrulha:
  ambiente: leve            # leve | gazebo | real
  modelo: standard          # standard | lite
  mapa: /caminho/mapa.yaml
  pose_inicial: {x: 0.0, y: 0.0, yaw_graus: 90}
  aproximacao_doca: {x: -1.0, y: 1.0, yaw_graus: 0}
  pontos:
    - {x: -5.0, y: 1.0, yaw_graus: 0}
  bateria:
    modo: absoluto          # absoluto (padrão se faltar) | relativo (PAT-21)
    alta: 0.95              # usados no modo absoluto
    baixa: 0.20
    critica: 0.10
    delta_alta: 0.005       # usados no modo relativo: limite = b0 - delta
    delta_baixa: 0.01
    delta_critica: 0.02
  tempos: {espera_bateria_s: 30, confirma_dock_s: 5, cancelar_s: 2,
           bateria_perdida_s: 10,   # 30 no gazebo (PAT-18)
           destino_s: 120, servidor_s: 30, encerrar_s: 3}
  limites: {falhas_seguidas: 3, tentativas_dock: 3}
  validacao: {margem_obstaculo_m: 0.25}
```

### Esquema do log (OBS-01)

Uma linha JSON por evento, em `~/.ros/patrulha/<data-hora>.jsonl`. Ao terminar, o arquivo é copiado para `workspace/logs/`.

| Campo | Obrigatório | Exemplo |
|---|---|---|
| `t` | Sim | horário em segundos (relógio do ROS: tempo simulado no leve e no Gazebo) |
| `t_parede` | Sim | horário em segundos do tempo de relógio (`time.time()`). É o que prova os prazos do TST-03 e do TST-08 |
| `evento` | Sim | da lista abaixo |
| `estado` | Sim | `iniciando`, `saindo_doca`, `patrulhando`, `indo_doca`, `encaixando`, `carregando`, `encerrando` |
| `bateria` | Sim (`null` se ainda não chegou) | 0,42 |
| `ponto` | Não | índice do ponto |
| `resultado` | Não | código do Nav2 ou da ação |
| `detalhe` | Não | texto livre (por exemplo, o motivo do VAL-02) |
| `b0` | Só em `limites_bateria` | 0,87 |
| `limites` | Só em `limites_bateria` | `{"alta": 0.865, "baixa": 0.86, "critica": 0.85}` |
| `hash_codigo`, `hash_config`, `versao`, `ambiente`, `modelo` | Só em `inicio` (OBS-03) | SHA-256 em hexadecimal |

Lista fechada de eventos:

- `inicio`
- `limites_bateria`
- `config_invalida`
- `sem_bateria`
- `fora_da_doca`
- `servidor_indisponivel`
- `undock_ok`
- `undock_falhou`
- `destino_enviado`
- `destino_ok`
- `destino_falhou`
- `destino_cancelado`
- `bateria_baixa`
- `bateria_critica`
- `bateria_perdida`
- `sem_relogio`
- `dock_ok`
- `dock_nao_confirmado`
- `dock_falhou`
- `carga_completa`
- `falhas_seguidas`
- `encerrado`
- `resumo`

Os códigos de saída estão no `DEFINE.md`.

## 2. Mudanças na base falsa (a base falsa, hoje `workspace/meu_ws/src/lab_tb4/lab_tb4/base_falsa.py`)

Também é um pedido separado. Tudo vale só para o leve. No Gazebo, a base falsa fica **desligada** por padrão, porque a Create 3 simulada já responde à bateria, à doca e às ações. Ela só volta, com uma das chaves abaixo, se a medição M-GZ mostrar que alguma dessas partes não funciona.

| Mudança | Para quê | Requisito |
|---|---|---|
| Publicar `/dock_status` **na hora** em `do_dock` e `do_undock`, e não só no `tick()` de 1 s | Decide a hipótese H2 e tira o falso erro | PAT-09 |
| Parâmetro `falhar_dock_n` (o dock falha nas N primeiras vezes) | Testar novas tentativas | TST-04 |
| Parâmetro `queda_bateria_em_s` e `queda_bateria_para` | Derrubar a bateria no meio do trecho | TST-05 |
| Chaves `simular_bateria`, `simular_doca` e `simular_amcl` | No Gazebo, ligar só a parte que faltar (por exemplo, a bateria, se o `/battery_state` não chegar) | AMB-01, PAT-04, PAT-20 |
| Parâmetro `comecar_na_doca` | Provocar o início fora da doca | PAT-17 |
| Parâmetro `parar_bateria_em_s` (a bateria deixa de ser publicada) | Provocar a perda da bateria | PAT-18 |

## 3. Escada de testes

Só se sobe de degrau quando o anterior passa. RAM e tempo de L0 a L2 vêm de `docs/historico/resultados-jazzy.md`, e o resto é estimativa.

| Degrau | O que roda | RAM | Tempo de relógio | Prova | Onde |
|---|---|---|---|---|---|
| **L0** | pytest em Python puro, com um navegador falso | desprezível | segundos | Toda a lógica, inclusive as falhas | Notebook, sem Docker |
| **L1** | Leve (`nav2_loopback_sim`), mapa pequeno, pontos a 1,5 a 3 m, descarga acelerada, falhas injetadas | cerca de 0,7 GiB | estimativa de 5 a 15 min por ciclo (a medir) | O nó com o Nav2 real, o ciclo de recarga e os caminhos de falha | Notebook, **o principal** |
| **L1b** | O mesmo L1 com `params_file:=` apontando para `turtlebot4_navigation/config/nav2.yaml` | cerca de 0,7 GiB (a medir) | igual ao L1 | Que a configuração do Nav2 do robô real funciona com o nosso nó (H4) | Notebook |
| **L2** | Leve no `warehouse`, com os pontos originais | cerca de 0,7 GiB | cerca de 20 min | Comparação com o `patrol_loop` oficial | Notebook, opcional |
| **L3** | Gazebo `maze`, sem janela e sem RViz, com Nav2 e AMCL reais, pontos curtos, base falsa desligada, `config/gazebo_maze.yaml` (modo relativo), "modo enxuto" | **desconhecida**: teto inicial de 3,5 GiB (ver M-GZ) | estimativa de 20 a 30 min por ciclo (TST-08 aceita até 60) | AMCL de verdade com lidar, a doca e a bateria da Create 3 simulada, e os tempos do Nav2 sob carga | Notebook, **recomendado**, se a medição M-GZ aprovar. Se não, servidor do INF |
| **L3-alt** | MVSim com o mapa em imagem (plano B, só se o L3 for inviável no notebook e não houver servidor) | desconhecida (o projeto diz ser leve) | desconhecido | AMCL com lidar e física 2D. A bateria e a doca continuam na base falsa | Notebook. Exige montar o robô e o launch, e mudar a imagem Docker |
| **L4** | Robô do INF | | | Tudo | INF |

Por que o L3 subiu de "opcional" para "recomendado": é o único degrau antes do INF em que a doca e a bateria **não são nossas**. São da iRobot, com as mesmas mensagens do robô real, e o AMCL pode errar a posição. O leve nunca mostra isso.

Conta do ciclo no L3 (estimativa, das taxas fixas de `robot_state.cpp` do `create3_sim`, branch `jazzy`):

| Etapa | Taxa | Tempo simulado | Relógio a 0,18 |
|---|---|---|---|
| Cair 1 ponto percentual andando (`b0` até `baixa`) | 0,0089% por segundo | cerca de 113 s | cerca de 10 min |
| Ir à doca e encaixar | | 30 a 60 s (estimativa) | 3 a 6 min |
| Carregar até `alta` (cerca de 0,7 a 1 ponto) | 0,0127% por segundo | 55 a 80 s | 5 a 7 min |
| Undock e mais 1 ponto | | 30 a 60 s (estimativa) | 3 a 6 min |
| **Total** | | cerca de 230 a 310 s | **cerca de 20 a 30 min** |

Se o L3 não couber no notebook, ele fica para o servidor do INF, sem bloquear o L4.

### Medição M-GZ (PENDENTE: decide se o L3 cabe no notebook)

Não foi feita. Fica para quando o Roberto pedir. Ela **não depende do pacote** `patrulha_tb4`: pode rodar antes dele, porque só mede o simulador.

**Preparo**

1. O Roberto fecha o navegador e os programas pesados.
2. `free -m`. Pela regra do TST-06, o teto do container pode ser no máximo a memória livre menos 1 GiB. Em 9/nov, com o Opera fechado, havia cerca de 4,5 a 5 GiB livres. Portanto, o teto realista é de **3,5 GiB**, e não de 4,5 como chegou a ser pensado.
3. Container com `--memory` e `--memory-swap` iguais a 3,5 GiB, GPU Intel e sem janela, como no `run_sim_headless.sh` da época (removido na migração para Humble; hoje o `lab.sh sim` e o `lab_tb4` fazem isso).

**Etapas** (cada uma num container novo, da mais leve para a mais pesada)

| Etapa | O que sobe | O que se mede | Como se mede |
|---|---|---|---|
| **E1** | Gazebo `world:=maze`, sem Nav2 e sem localização | Fator de tempo real, pico de RAM, `/battery_state`, `/dock_status` no início, lidar | O fator de tempo real é o avanço do `/clock` dividido pelo relógio, em janelas de 60 s (o método de 5/nov usava 10 s). O pico de RAM vem do `docker stats` amostrado a cada 5 s. A bateria: esperar **pelo menos 3 min de relógio** e contar as mensagens (a 0,18 do tempo real, devem chegar cerca de 3). A doca: o primeiro `/dock_status` deve dizer `is_docked: true`, se o robô nasce na doca (a conferir). O lidar: mínimo, máximo e quantos raios valem 0,16 m, com um script que assine os tópicos com QoS `best_effort` (o `sensores.py` da época não foi mantido) |
| **E2** | O mesmo, com `localization:=true nav2:=true` e o mapa do `maze` (conferir o nome do argumento do mapa no launch antes) | Os mesmos números, mais um destino de 2 m | Pose inicial pelo `/initialpose`. Depois, um destino a 2 m enviado à mão (`ros2 action send_goal /navigate_to_pose ...`), cronometrando o relógio. Procurar no log do Nav2 erros de tempo (`transform timeout`, `extrapolation`, `patience exceeded`) |
| **E3** (opcional) | E2 sem a câmera OAK-D | Quanto o fator de tempo real melhora | Exige uma cópia nossa do URDF sem o `oakd`. Por isso é um pedido separado |

**Critério de decisão** (valores propostos, a ajustar)

| Resultado | Decisão |
|---|---|
| Sem OOM em E2, notebook usável, fator de tempo real de pelo menos `[0,10]` com o Nav2, destino de 2 m com sucesso e sem erros de tempo, `/battery_state` chegando e lidar variando com as paredes | **L3 no notebook**: segue para o TST-08 |
| OOM com 3,5 GiB | Repetir E2 com 4 GiB **só se** houver pelo menos 5 GiB livres. Se não, o L3 vai para o servidor do INF |
| Fator de tempo real abaixo de 0,10, ou erros de tempo do Nav2 | Tentar E3 (sem câmera). Se não melhorar, o L3 vai para o servidor do INF, ou para o L3-alt (MVSim) |
| Lidar com todos os raios em 0,16 m também no `maze` | O AMCL não funciona: o L3 trava até explicar o lidar (hipótese a testar: o lidar acerta o próprio corpo do robô) |
| `/battery_state` não chega nem em 3 min | Ligar só a `simular_bateria` da base falsa e seguir, anotando a perda de realismo. Essas execuções testam o resto (doca e AMCL), mas **não contam como TST-08** |
| O robô não nasce na doca (primeiro `/dock_status` com `is_docked: false`) | Procurar no launch os argumentos de pose de nascimento do robô e da doca. Se não houver como, o L3 trava, porque o PAT-17 encerraria com o código 6 |

**Registro:** uma linha no documento da tarefa (`docs/tarefas/`) e os arquivos (CSV do `docker stats`, logs e números do lidar) em `workspace/logs/`.

**Tempo previsto:** cerca de 15 min para E1 e 30 min para E2, ou cerca de 1 h com o preparo.

### "Modo enxuto" (script a criar depois: `teste_enxuto.sh` em `infra/docker/`)

1. Pede para fechar o navegador e os programas pesados, e mostra o `free -m`.
2. Recusa subir se a memória livre for menor que o teto mais 1 GiB (TST-06).
3. Sobe o container com `--memory` e `--memory-swap` iguais ao teto, sem RViz e sem janela do Gazebo (Xvfb ou modo sem janela, como no `run_sim_headless.sh` da época (removido na migração para Humble; hoje o `lab.sh sim` e o `lab_tb4` fazem isso)).
4. Grava o pico do `docker stats` e o log JSONL em `workspace/logs/`.
5. Para tudo ao terminar, ou com Ctrl+C.

## 4. Kit de campo do INF

Um checklist em `specs/patrol-inf/kit-de-campo.md`, a escrever depois da aprovação. Os nomes dos launches são do pacote `turtlebot4_navigation` (`slam.launch.py`, `localization.launch.py` e `nav2.launch.py`, que estão na imagem). Os detalhes de rede estão no manual, seção "Simple Discovery", a reler antes da visita.

| Etapa | Feito quando |
|---|---|
| 1. Rede: mesmo `ROS_DOMAIN_ID` e middleware, e o PC enxerga `/battery_state`, `/scan` e `/dock_status` | `ros2 topic echo /battery_state --once` responde no PC. Anotar a frequência (`ros2 topic hz /battery_state`) e o maior intervalo, para o `bateria_perdida_s` do real (PAT-18) |
| 2. Teleop | O robô anda e para pelo comando |
| 3. Dock e undock manual (`ros2 action send_goal /undock ...` e `/dock`) | Os dois dão sucesso e o `/dock_status` muda |
| 4. SLAM **começando com o robô na doca** (H3), percorrer o laboratório e salvar o mapa | `lab.yaml` e `lab.pgm` gravados |
| 5. Localização e Nav2 com o perfil `nav2_inf_devagar.yaml` (INF-02) | Um destino pelo RViz chega |
| 6. Escolher os pontos e a aproximação da doca (de frente para a doca, a cerca de 0,5 a 1 m, a confirmar) no RViz, e preencher `inf_lab.yaml` | `validar_pontos` passa (protocolo, item 1) |
| 7. Patrulha com 1 ponto | Vai e volta |
| 8. Patrulha completa e devagar | 1 volta sem intervenção |
| 9. Ciclo de recarga com limites temporários (H5, por exemplo, "baixa" igual à carga atual menos 2%) | O ciclo fecha |
| 10. Aceite (INF-03), com o rosbag (INF-04) | Os números combinados com o coordenador |

Ficam com o robô o tempo todo (protocolo, item 2): uma pessoa ao lado, a área livre e o comando de parar à mão. O `Ctrl+C` no nó cancela a ação ativa (PAT-15). Uma parada de segurança invalida a execução de aceite (INF-03).

## 5. Os três pilares

| Pilar | Como fica | Débito declarado |
|---|---|---|
| **Identidade** (quem e qual versão rodou) | OBS-03: a versão do pacote, o hash do código instalado (prova do AMB-01 sem depender de git), o hash da configuração, o ambiente e o modelo do robô no início do log | O projeto **não é repositório git**, então não há o hash do commit. Recomendação: `git init` (decisão do Roberto) |
| **Observabilidade** (está funcionando?) | Log JSONL, resumo final e rosbag no INF. O pico de RAM nos testes locais | Sem painel ao vivo. Basta para a primeira entrega |
| **Rastreabilidade** (por que fez isso?) | Tabela abaixo, que liga cada requisito ao teste. Evidências de cada execução em `workspace/logs/` | INF-02 a INF-04 e o protocolo só se provam no INF |

### Requisito → teste

| Requisitos | L0 (pytest) | L1 | L3 | L4 (INF) |
|---|---|---|---|---|
| PAT-01, TST-07 | Sim (lint) | | | |
| PAT-03, PAT-04 | Sim | Sim (base falsa com a bateria desligada) | Sim (bateria da Create 3 a 0,1 Hz) | |
| PAT-05, PAT-06, PAT-14 | Sim | Sim (TST-05) | Sim (TST-08, PAT-06) | Sim (H5) |
| PAT-21, PAT-21b | Sim | | Sim (TST-08) | Sim (kit de campo, etapa 9) |
| PAT-07, PAT-07b, PAT-08, PAT-19 | Sim | Sim (ponto inalcançável na configuração de teste) | | |
| PAT-09 a PAT-11 | Sim | Sim (TST-04) | Sim (doca da Create 3 simulada) | Sim |
| PAT-12, PAT-13 | Sim | Sim (TST-03) | Sim (TST-08) | Sim |
| PAT-15, PAT-16 | Sim | Sim | | Sim |
| PAT-17 | Sim | Sim (base falsa começando fora da doca) | | |
| PAT-18, PAT-18b | Sim | Sim (base falsa para de publicar a bateria, fora e dentro da doca) | | |
| PAT-22 | Sim | Sim (subir o nó com `use_sim_time` e sem simulador) | | |
| PAT-20 | Sim | Sim (sem a base falsa, então sem `/dock`) | | |
| VAL-01 a VAL-04 | Sim | | | Sim (protocolo, item 1) |
| AMB-01, AMB-02 | | Sim | Sim | Sim |
| AMB-03 | | Sim (L1 sem RViz) | | |
| OBS-01 a OBS-03 | Sim | Sim | | Sim |
| TST-06 | | Sim (script) | Sim | |
| TST-08 | | | Sim | |
| INF-02 a INF-04 | | | | Sim |

## 6. Ordem de trabalho proposta (pedidos separados)

1. Base falsa: publicar `/dock_status` na hora, e repetir o `patrol_loop` oficial no leve. Isso decide a hipótese H2.
2. `decisao.py`, `config.py`, `pontos.py` e `registro.py` com os testes (L0).
3. `no_patrulha.py` e o launch, com o L1 no mapa reduzido.
4. As falhas injetadas na base falsa (TST-04 e TST-05).
5. O L1b com o `nav2.yaml` do TurtleBot 4.
6. O kit de campo.
7. O L3 (TST-08), se a medição M-GZ aprovar.

A medição M-GZ (pendente) corre por fora dessa fila: pode ser feita a qualquer momento, quando o Roberto pedir. Quanto antes, melhor, porque ela decide se o passo 7 acontece no notebook.

## 7. Decisões abertas

| Decisão | Quem decide | Efeito no design |
|---|---|---|
| A patrulha roda no PC ou no Raspberry Pi | Roberto e a equipe, depois de testar no INF | Nenhum no código. Muda só o kit de campo. Vira um ADR depois |
| Modelo Standard ou Lite | Coordenador | O campo `modelo` da configuração |
| "Pronto" é em simulação ou no robô | Coordenador | Se for em simulação, o aceite para no L1 e no L1b |
| Middleware e discovery do robô | Equipe do INF | O checklist de rede |
| Números do aceite (voltas, ciclos, velocidade) | Coordenador | Os valores entre colchetes do `DEFINE.md` |
| O L3 roda no notebook, no servidor do INF ou no MVSim (L3-alt) | A medição M-GZ (pendente) | Onde roda o TST-08. O código não muda em nenhum dos casos |

## Efeito prático

Os degraus L0 e L1 testam a lógica e os caminhos de falha, por menos de 1 GiB e em minutos. O L3 (Gazebo `maze` enxuto) é o único teste local com a doca, a bateria e o AMCL de verdade. Ele é recomendado, mas depende da medição M-GZ, e não bloqueia a ida ao INF. O mesmo código passa pelos três ambientes. No laboratório, o trabalho se resume aos 10 passos do kit de campo.

## Adendo (2026-11-18): níveis de teste depois da migração para Humble

Origem: `specs/migracao-humble/` (DOC-03), ADR-001 (tudo em Humble) e ADR-002 (Gazebo no PC do laboratório como simulador principal). Este adendo não muda nenhum requisito PAT, VAL, OBS ou TST nem a tabela "Requisito → teste". Ele muda **onde** cada nível roda.

| Nível | O que é | Onde roda | Como |
|---|---|---|---|
| L0 | pytest da lógica, sem ROS | Notebook, PC e CI (imagem `ros:humble-ros-base`) | `python3 -m pytest` no `patrulha_tb4` e no `lab_tb4` |
| L1 | Simulador leve: `nav2_loopback_sim` vendorizado (`workspace/meu_ws/src/terceiros/`) e base falsa, com os 11 cenários de injeção de falhas | PC do laboratório (`physical-ai:sim`) | `infra/docker/teste_l1.sh <cenario>`, que sobe o `lab_tb4/launch/l1.launch.py` |
| L3 | Gazebo (Ignition Fortress) sem janela, com a Create 3 simulada e o AMCL de verdade. **O simulador principal** desde o ADR-002 | PC do laboratório | `infra/docker/lab.sh sim subir gazebo ...` (`lab_tb4/launch/gazebo.launch.py`) |
| L4 | Robô real | PC do laboratório + TurtleBot 4 | `infra/docker/lab.sh robo ...`, só depois da V5 da spec `migracao-humble` |

O que mudou em relação ao texto acima:

- O notebook deixou de simular. As notas sobre o limite de 7,4 GiB valem só para ele.
- A medição **M-GZ** (seção 3, pensada para o notebook e para o Gazebo Harmonic do Jazzy) passa a ser a **M-GZH**: os mesmos critérios (fator de tempo real, pico de RAM, `/battery_state`, doca, lidar com obstáculo e um destino de 2 m), medidos no PC do laboratório com o Fortress. Ela continua só com pedido explícito do Roberto. Se reprovar, o ADR-002 é revisto e o L1 volta a ser o principal.
- O `l1_dentro.sh` e o `treino_leve.sh` citados acima saíram. Os cenários são os mesmos, agora em `lab_tb4/config/cenarios_l1.yaml`. O único desvio é o `l1b` (`docs/tarefas/2026-11-18-f3-l1-leve.md`).
- Os caminhos `/opt/ros/jazzy/...` das configurações viraram `pkg://turtlebot4_navigation/maps/...` (CFG-01 da `migracao-humble`).

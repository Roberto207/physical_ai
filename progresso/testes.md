# Testes realizados

Origem de cada dado: **5/nov** vem do registro anterior; **9/nov** e **12/nov** foram observados diretamente nas sessões. Nenhum teste rodou no robô real nem no INF.

## Máquina

| Item | Valor |
|---|---|
| SO | Lux 2 (base Debian). Não é Ubuntu |
| RAM | 7,4 GiB (cerca de 4,5 a 5 GiB disponíveis com o Opera fechado) |
| GPU | Intel integrada, sem NVIDIA |
| Docker | 29.9.2 |

## 1. Testes em Python puro (5/nov)

`workspace/exemplos/decisao_patrulha.py` (decisão da patrulha) e `validar_acao.py` (validador de ações da LLM), sem ROS. **19 testes passam.** Servem porque rodam em milissegundos, enquanto cada teste na simulação leva minutos.

## 2. turtlesim (5/nov)

Topic e action funcionam. Serviu para aprender nodes, topics, services e actions.

## 3. Gazebo sem janela (5/nov)

Mundo `empty`, modelo `standard`, sem Nav2, 2,5 GiB e 4 CPUs.

| Modo | RTF | `/scan` | `/odom` | RAM | Resultado |
|---|---|---|---|---|---|
| Xvfb (tela virtual, CPU) | cerca de 0,05 | 2,3 Hz | 2,4 Hz | 1,6 GiB | Roda. Robô não saiu do lugar em 4 s |
| GPU Intel | cerca de 0,18 | 8,8 Hz | 8,3 Hz | 1,9 GiB | Roda. Andou 6,4 cm em 8 s |

O RTF vem de uma janela de 10 s por modo: é ordem de grandeza.

Problemas resolvidos na montagem: pacote apt dos tutoriais inexistente para Jazzy (compilado do GitHub), erro `Couldn't open X display` (Xvfb), `xvfb-run` travando (`docker run --init`), `gz_args` ignorado (cópia do launch em `infra/docker/sim_headless.launch.py`). Detalhes em `contexto/infra/teste-simulacao-2026-11-05.md`.

## 4. Gazebo com janela

| Data | Teto de RAM | Resultado |
|---|---|---|
| 5/nov | 2,5 GiB | Falhou: `OOMKilled=true`, relógio parado em 0 |
| **9/nov** | **3,5 GiB** | **Funcionou:** 2,6 GiB usados, 4 CPUs saturadas, sem OOM |

Em 9/nov foi preciso fechar o Opera (tinha cerca de 5 GiB de RAM disponíveis depois disso). Com o Opera aberto havia só 2,4 GiB disponíveis e o swap estava em 3,7 GiB de 5, e por isso o teste foi adiado.

### Sensores no Gazebo (9/nov, medição de 20 s)

| Sensor | Tópico | Resultado | Taxa (relógio real) |
|---|---|---|---|
| Lidar | `/scan` | 640 raios, -180° a 180°, 0,16 a 12 m | cerca de 5,9 Hz |
| Câmera | `/oakd/rgb/preview/image_raw` | 320 x 240, `rgb8` | cerca de 2,9 Hz |

- Os sensores usam QoS `best_effort`. O `ros2 topic hz` simples dizia "não publicado", e por isso o script `evidencias/sensores.py` foi necessário.
- Foto da câmera: `evidencias/gazebo-camera-oakd.png`. Mostra céu cinza, chão claro e um objeto escuro e arredondado embaixo, no centro, que **não foi identificado**.
- **Estranheza aberta:** os 640 raios do lidar voltaram todos com 0,16 m (o mínimo), num mundo vazio. Hipóteses não testadas: o simulador devolve o mínimo quando nada é atingido, ou os raios batem no próprio robô ou na base. Teste: pôr uma caixa na frente.
- Tópicos do robô vistos: `/odom`, `/cmd_vel` (via `/diffdrive_controller/cmd_vel`), `/battery_state`, `/dock_status`, `/bumper_contact`, `/hmi/...`, câmera e lidar.

### Não registrado em 9/nov

Mensagens em `/battery_state`, undock/dock no Gazebo e movimento do robô por `/cmd_vel` não foram medidos nesta sessão. A bateria no Gazebo continua sendo pendência (em 5/nov nenhuma mensagem chegou em 8 a 10 s).

## 5. Simulador leve com Nav2 (5/nov e 9/nov)

Mapa `warehouse`, base e bateria falsas (`fake_tb4_base.py`).

| Item | 5/nov | 9/nov |
|---|---|---|
| RAM | cerca de 0,5 GiB, 0,9 com RViz | 0,53 GiB ao subir, 0,69 GiB com a patrulha |
| CPU | cerca de 2 núcleos | 53% ao subir |
| Navegação | Falhou até `(-5, 1)` após 209 s (14 `Failed to make progress`) | **Funcionou** em todos os destinos |
| Docking | Nunca rodou | **Rodou** (ver `patrol-loop.md`) |
| Janela do RViz | Não confirmada | Não confirmada |

- Na subida de 9/nov o log repetiu `frame "map" does not exist` até a pose inicial ser definida. A patrulha define a pose sozinha. Sem ela, a pose precisa ser marcada no RViz (2D Pose Estimate).
- O `collision_monitor` avisou várias vezes que o `scan` estava atrasado cerca de 1 s e ignorou a fonte. É sintoma de lentidão e não foi investigado.
- Causas da falha de 5/nov **descartadas**: CPU (3 e 8 núcleos iguais), obstáculo no mapa, camada `StaticLayer` do costmap. **Não testado:** trocar o controlador MPPI.
- Como a falha não se repetiu em 9/nov, não dá para afirmar que está resolvida, nem que era intermitente. Falta repetir.

## 6. Spec `patrol-inf`: testes de 12/nov

Origem: observado diretamente na sessão de 12/nov. Detalhes de cada mudança em `../docs/registro-de-mudancas.md`. Nada rodou no robô real.

### 6.1 L0: lógica em Python puro, no notebook, sem ROS

| Item | Resultado |
|---|---|
| Suíte do pacote `patrulha_tb4` (`workspace/meu_ws/src/patrulha_tb4/test/`) | **124 testes passam em 0,3 s** (limite do TST-01: 10 s) |
| Rastreio (`test/checar_rastreio.py`) | Os 31 requisitos marcados como L0 no DESIGN têm teste |
| Lint de poses (TST-07) | Nenhum arquivo do pacote escreve pose no código |
| `validar_pontos` nas 4 configurações do pacote | Aprovadas contra os mapas `maze` e `warehouse` da imagem |

### 6.2 Hipótese H2: o falso `Robot failed to dock`

Com a base falsa publicando o `/dock_status` na hora do dock (antes, só no tique de 1 s), o `patrol_loop` oficial, sem alteração, passou de `Dock succeeded` para `Charging...`. **H2 confirmada:** o erro de 9/nov vinha da nossa base falsa. Condições: bateria inicial de 16%, para ir à doca logo depois do undock. Log em `evidencias/patrol_loop-leve-2026-11-12-h2.log`.

Isso não diz nada sobre a doca real: no robô, o tempo até o `is_docked: true` precisa ser medido (kit de campo, etapa 3).

### 6.3 L1: o nosso nó no simulador leve (`infra/docker/teste_l1.sh`), 12 e 13/nov

Mapa `maze`, pontos a 1,5 a 2,5 m, base e bateria falsas, sem RViz, teto de 2 GiB. A tabela traz a execução que vale de cada cenário. As execuções reprovadas ou inválidas também estão guardadas em `evidencias/l1/`, e explicadas em `../docs/registro-de-mudancas.md`.

| Cenário | Requisito | Veredito | Número medido | Pico de RAM |
|---|---|---|---|---|
| `ciclo` (13/nov) | TST-03, PAT-12, PAT-13, AMB-03 | Aprovado | Ciclo de recarga em 386 s (limite: 900 s) | 656 MiB |
| `l1b` (13/nov) | H4 | Aprovado | Ciclo em 383 s com o `nav2.yaml` do TurtleBot 4 | 468 MiB |
| `dock_falha` (13/nov) | TST-04, PAT-09, PAT-10 | Aprovado | `dock_ok` na 2ª tentativa, 2 s depois da falha | 444 MiB |
| `queda_bateria` (12/nov) | TST-05, PAT-06 | Aprovado | Reação em 0,03 s (limite: 2 s) | 472 MiB |
| `sigint` (13/nov) | PAT-15 | Aprovado | Do Ctrl+C ao resumo em 0,11 s (limite: 3 s) | 471 MiB |
| `bateria_perdida` (13/nov) | PAT-18, PAT-18b | Aprovado | Volta à doca e código 3 | 459 MiB |
| `falhas_seguidas` (13/nov) | PAT-07, PAT-08, PAT-19 | Aprovado | 3 destinos falhos, dock e código 7 | 437 MiB |
| `fora_da_doca` (12/nov) | PAT-17 | Aprovado | Código 6 em 4,8 s | 412 MiB |
| `sem_bateria` (12/nov) | PAT-03, PAT-04 | Aprovado | Código 3 em 30,4 s | 413 MiB |
| `sem_servidor` (12/nov) | PAT-20 | Aprovado | Código 8 em 30,6 s | 412 MiB |
| `sem_relogio` (12/nov) | PAT-22 | Aprovado | Código 9 em 10,2 s | 172 MiB |

Todas as execuções a partir de 23:26 de 12/nov têm o mesmo hash de código (AMB-01).

Três coisas que os testes ensinaram:

1. **Cancelar e reenviar na mesma hora não funciona no Nav2.** No primeiro `ciclo` (12/nov), o destino da doca enviado logo depois do cancelamento foi abortado. O nó passou a esperar o cancelamento terminar, e o problema sumiu.
2. **O `nav2.yaml` do TurtleBot 4 manda a velocidade com carimbo de tempo.** No leve, o simulador precisa da chave `enable_stamped_cmd_vel: true`, senão o robô simulado não anda. O `l1b` monta esse arquivo sozinho.
3. **O Nav2 leve às vezes não sobe** ("Failed to activate local_costmap because transform from base_link to odom did not become available"): 2 vezes em 16 subidas, com e sem carga no notebook. Causa não confirmada. O script do L1 agora tenta de novo sozinho, mas essa nova tentativa ainda não foi exercitada.

Limite de tudo isso: bateria, doca e AMCL são falsos. O L1 prova o nosso nó com o Nav2 de verdade, e não o comportamento do robô real.

## 7. Cuidados que valem para todos os testes

- Nunca usar `docker build` com o `Dockerfile` do projeto (sem limite de memória). A imagem foi feita com `docker run --memory=2g` e `docker commit`.
- Fechar o navegador antes de abrir o Gazebo com janela.
- Terminou: `treino_leve.sh parar` ou `docker rm -f tb4gui`, e `xhost -SI:localuser:root`.
- O erro `RTPS_TRANSPORT_SHM ... Failed init_port` do DDS aparece depois de matar processos ROS à força e é inofensivo para o que vimos.

## Efeito prático

Os resultados de 9/nov mudam duas linhas do registro antigo: "docking nunca rodou" virou "rodou" e "navegação falha" virou "funcionou desta vez, causa da falha antiga desconhecida". O que continua dependendo do INF é o realismo (Nav2 dentro do Gazebo e o robô real).

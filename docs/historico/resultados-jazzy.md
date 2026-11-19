# Resultados da época do Jazzy (5 a 13/nov/2026)

**Histórico congelado.** Resume o que foi medido no notebook com ROS 2 Jazzy, antes da migração para Humble (ADR-001). Os caminhos e os números são da época; nada aqui é atualizado. O código dessa época está na tag `jazzy-final`. Nada rodou no robô real nem no INF: base, bateria e AMCL do simulador leve eram falsos, então estes resultados provam a lógica do nosso nó com o Nav2, e não o comportamento do robô.

Origem: resumo dos textos `testes.md`, `patrol-loop.md` e `proximos-degraus.md` da pasta `progresso/` (fora do git), mais as pendências fechadas de `contexto/pendencias.md`.

## 1. Máquina de teste

Notebook com Lux 2 (base Debian), 7,4 GiB de RAM (4,5 a 5 GiB livres com o navegador fechado), GPU Intel integrada, Docker 29.9.2.

## 2. Medições de 5 e 9/nov

| Teste | Resultado |
|---|---|
| Lógica em Python puro | 19 testes (decisão da patrulha e validador de ações) passavam em milissegundos |
| Gazebo sem janela, mundo `empty`, 2,5 GiB, 4 CPUs | Xvfb (CPU): RTF cerca de 0,05, `/scan` a 2,3 Hz, 1,6 GiB. GPU Intel: RTF cerca de 0,18, `/scan` a 8,8 Hz, 1,9 GiB. O RTF vem de uma janela de 10 s: é ordem de grandeza |
| Gazebo com janela | 5/nov com teto de 2,5 GiB: `OOMKilled=true`. 9/nov com teto de 3,5 GiB e o navegador fechado: 2,6 GiB usados, sem OOM |
| Sensores no Gazebo (9/nov, 20 s) | Lidar `/scan`: 640 raios, 0,16 a 12 m, cerca de 5,9 Hz. Câmera OAK-D: 320 x 240 `rgb8`, cerca de 2,9 Hz. QoS `best_effort` (o `ros2 topic hz` simples não mostra) |
| Simulador leve com Nav2, mapa `warehouse` | 0,53 GiB ao subir, 0,69 GiB com a patrulha. Em 5/nov a navegação falhou até `(-5, 1)` após 209 s; em 9/nov funcionou em todos os destinos. A causa da falha de 5/nov nunca foi achada (CPU, obstáculo e `StaticLayer` descartados) |

Pontos que ficaram abertos nessas medições (seguem em aberto): o lidar do Gazebo devolveu os 640 raios em 0,16 m num mundo vazio, e a bateria do Gazebo não entregou mensagem em 8 a 10 s.

## 3. O `patrol_loop` oficial (pacote `turtlebot4_python_tutorials`)

Percorre pontos em loop e, com bateria baixa, volta à doca para carregar. Rodou inteiro no simulador leve em 9/nov (bateria inicial 30%, descarga de 0,1% por segundo, carga de 5% por segundo, mapa `warehouse`).

**Três defeitos achados lendo o código (5/nov):**

| # | Defeito | Consequência | Onde foi resolvido |
|---|---|---|---|
| 1 | `battery_percent` só existe depois da primeira mensagem | `AttributeError` se o laço chegar antes | `patrulha_tb4`: espera a primeira bateria (PAT-03, PAT-04) |
| 2 | Bateria só lida entre destinos, porque `startToPose` trava | Num trecho longo a bateria zera sem reação | `patrulha_tb4`: usa `goToPose` e `isTaskComplete` e checa a bateria durante o trajeto (PAT-06) |
| 3 | Ignora o resultado de cada destino | Destino falho é pulado sem contagem | `patrulha_tb4`: conta falhas seguidas (PAT-07, PAT-08, PAT-19) |

**O que a execução de 9/nov mostrou:**

- O defeito 2 apareceu ao vivo: a bateria foi de 19,9% a 0% no trecho de volta (cerca de 255 s), porque o programa só leu a bateria ao fim de cada destino.
- O caminho de docking rodou pela primeira vez.
- O `Robot failed to dock` depois de `Dock succeeded` era da nossa base falsa, que atualizava o `/dock_status` só no tique de 1 s. Em 12/nov a base passou a publicar na hora do `do_dock`; o `patrol_loop` oficial, sem alteração, chegou a `Charging...` (hipótese H2 confirmada, bateria inicial de 16%). Não diz nada sobre a doca real.
- Fatos do código: `isDockComplete()` e `isUndockComplete()` devolvem `True` mesmo quando a ação falha; `waitUntilNav2Active()` espera o nó `amcl` e uma `/amcl_pose` (por isso o leve finge o AMCL); o loopback do Nav2 publica pose perfeita e um `/scan` calculado contra o mapa, então o leve nunca testa um robô perdido; por padrão o leve usa os parâmetros do `nav2_bringup`, e não os do TurtleBot 4.
- Problemas do `patrol_loop` para o INF: pontos e pose inicial fixos do `warehouse`, bateria crítica só encerra o programa (o robô para onde estiver).

## 4. Testes da spec `patrol-inf` (12 e 13/nov)

**L0** (Python puro, notebook, sem ROS): suíte do `patrulha_tb4` com 124 testes em 0,3 s (limite do TST-01: 10 s); os 31 requisitos marcados como L0 no DESIGN tinham teste; `validar_pontos` aprovou as 4 configurações contra `maze` e `warehouse`.

**L1** (nosso nó no simulador leve, `teste_l1.sh`): mapa `maze`, pontos a 1,5 a 2,5 m, base e bateria falsas, sem RViz, teto de 2 GiB. A execução que vale de cada cenário:

| Cenário | Requisito | Veredito | Número medido | Pico de RAM |
|---|---|---|---|---|
| `ciclo` (13/nov) | TST-03, PAT-12, PAT-13, AMB-03 | Aprovado | Ciclo de recarga em 386 s (limite 900 s) | 656 MiB |
| `l1b` (13/nov) | H4 | Aprovado | Ciclo em 383 s com o `nav2.yaml` do TurtleBot 4 | 468 MiB |
| `dock_falha` (13/nov) | TST-04, PAT-09, PAT-10 | Aprovado | `dock_ok` na 2ª tentativa, 2 s depois da falha | 444 MiB |
| `queda_bateria` (12/nov) | TST-05, PAT-06 | Aprovado | Reação em 0,03 s (limite 2 s) | 472 MiB |
| `sigint` (13/nov) | PAT-15 | Aprovado | Ctrl+C ao resumo em 0,11 s (limite 3 s) | 471 MiB |
| `bateria_perdida` (13/nov) | PAT-18, PAT-18b | Aprovado | Volta à doca e código 3 | 459 MiB |
| `falhas_seguidas` (13/nov) | PAT-07, PAT-08, PAT-19 | Aprovado | 3 destinos falhos, dock e código 7 | 437 MiB |
| `fora_da_doca` (12/nov) | PAT-17 | Aprovado | Código 6 em 4,8 s | 412 MiB |
| `sem_bateria` (12/nov) | PAT-03, PAT-04 | Aprovado | Código 3 em 30,4 s | 413 MiB |
| `sem_servidor` (12/nov) | PAT-20 | Aprovado | Código 8 em 30,6 s | 412 MiB |
| `sem_relogio` (12/nov) | PAT-22 | Aprovado | Código 9 em 10,2 s | 172 MiB |

**O que os testes ensinaram:**

1. Cancelar e reenviar um destino na mesma hora não funciona no Nav2: o destino enviado logo após o cancelamento foi abortado. O nó passou a esperar o cancelamento terminar.
2. O `nav2.yaml` do TurtleBot 4 manda a velocidade com carimbo de tempo. No leve é preciso `enable_stamped_cmd_vel: true`, senão o robô simulado não anda (o `l1b` monta esse arquivo sozinho).
3. O Nav2 leve às vezes não subia ("transform from base_link to odom did not become available"): 2 vezes em 16 subidas, com e sem carga. Causa não confirmada, e a nova tentativa automática do script nunca foi exercitada.

## 5. Cuidados da época

- Nunca usar `docker build` com o `Dockerfile` sem limite de memória no notebook; a imagem da época foi feita com `docker run --memory=2g` e `docker commit`.
- Fechar o navegador antes do Gazebo com janela.
- O erro `RTPS_TRANSPORT_SHM ... Failed init_port` do DDS aparece depois de matar processos ROS à força e é inofensivo.

## 6. Pendências fechadas, movidas de `pendencias.md`

- Versão do ROS e distro padronizadas: **Humble em tudo** (ADR-001, 2026-11-18). Em 2026-11-16, Jazzy no PC e Humble no robô derrubou o robô.
- Simulação sem janela no Docker: cerca de 5% do tempo real com CPU e 18% com GPU Intel.
- Janela do Gazebo com GPU Intel: OOM com 2,5 GiB; com 3,5 GiB e o navegador fechado funcionou (2,6 GiB).
- Compilar `turtlebot4_python_tutorials` e `turtlebot4_openai_tutorials` do GitHub (não havia apt para Jazzy).
- Links do PDF do colega extraídos (estavam em `estudo/fontes.md`).
- Caminho de docking do `patrol_loop` e da base falsa: rodou em 2026-11-09.
- `Robot failed to dock` logo após `Dock succeeded`: base falsa (seção 3).
- Spec `patrol-inf`: pacote `patrulha_tb4` com a suíte L0 (124 testes, 0,3 s), H2 decidida, os 10 cenários L1 aprovados em 12 e 13/nov e o L1b aprovado (H4 confirmada).
- Como o PC fala com o robô real: configurado em 2026-11-16 (Humble, Discovery Server id 1, domínio 0, namespace `/robot1`); `lab.sh robo checar-rede` com `REDE OK`.
- Imagens no PC do lab em 2026-11-16: `physical-ai:robo` (5,37 GB) e `physical-ai:sim` (5,81 GB).

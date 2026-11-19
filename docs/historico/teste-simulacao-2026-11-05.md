# Teste de simulação na máquina do Roberto (2026-11-05)

## Resultado em uma linha

O TurtleBot 4 sobe no Gazebo dentro do Docker, sem janela e dentro de 2,5 GiB de RAM. Roda a cerca de **18% do tempo real** com a GPU Intel e cerca de 5% só com a CPU. É lento demais para testar o Nav2 de forma confortável, o que apoia a decisão de simular no INF. Nav2 ainda não foi testado.

## Atualização de 2026-11-09 (detalhes em `progresso/`)

Resultados novos, observados diretamente na sessão de 9/nov:

- **Gazebo com janela funcionou com teto de 3,5 GiB** (usou 2,6 GiB, sem OOM, 4 CPUs saturadas). O OOM de 5/nov valia só para o teto de 2,5 GiB. Foi preciso fechar o Opera antes.
- **Lidar e câmera chegam** no Gazebo: `/scan` a cerca de 5,9 Hz e câmera 320 x 240 a cerca de 2,9 Hz (relógio real). **Estranheza aberta:** os 640 raios do lidar voltaram todos com 0,16 m (o alcance mínimo) num mundo vazio.
- **`patrol_loop` rodou no simulador leve com bateria inicial de 30% e descarga de 0,1% por segundo.** Concluiu os três destinos, inclusive `(-5, 1)`, que falhava em 5/nov. Com 19,9% decidiu "Docking for charge" e voltou à base. A causa da falha de 5/nov **não foi encontrada** e o erro **não foi reproduzido**.
- **O caminho de docking rodou pela primeira vez.** A action `/dock` respondeu `Dock succeeded`, mas o programa logou `Robot failed to dock` e parou (linha 115 do `patrol_loop.py`). Hipótese, não confirmada: a checagem de `getDockedStatus()` veio antes da atualização do `/dock_status` da base falsa. Minutos depois o tópico mostrava `is_docked: true`.
- **O defeito 2 apareceu ao vivo:** a bateria foi de 19,9% a 0% no trecho de volta, sem reação até chegar.
- Log completo em `progresso/evidencias/patrol_loop-leve-2026-11-09.log`.

## Comparação dos três modos

Todos com mundo `empty`, modelo `standard` (o padrão do launch; a primeira versão deste arquivo dizia `lite`, errado), sem Nav2 e sem RViz, limitados a 2,5 GiB de RAM e 4 CPUs. O RTF vem de uma única janela de 10 s em cada modo, então é uma ordem de grandeza, não uma medida precisa.

| Modo | RTF | `/scan` | `/odom` | RAM do container | Resultado |
|---|---|---|---|---|---|
| Sem janela, tela virtual Xvfb (renderização por CPU) | cerca de 0,05 | 2,3 Hz | 2,4 Hz | 1,6 GiB | Roda. Robô não saiu do lugar em 4 s de comando |
| Sem janela, GPU Intel (`DISPLAY=:1`, `/dev/dri`) | cerca de 0,18 | 8,8 Hz | 8,3 Hz | 1,9 GiB | Roda. Robô andou 6,4 cm na odometria em 8 s de comando |
| Com janela do Gazebo, GPU Intel | não medido | sem dados | sem dados | bateu em 2,44 GiB | Falhou: OOM dentro do container (`OOMKilled=true`). Relógio parado em 0 |

A RAM disponível do notebook ficou acima de 2,3 GiB nos três modos. O cortador automático não foi acionado.

Com janela, o resultado vale só para o limite de 2,5 GiB. Com um teto maior pode funcionar, mas isso não foi testado.

Ainda não verificado: nenhuma mensagem de `/battery_state` chegou em nenhum modo (espera de 8 a 10 s). Pode ser só a lentidão ou um problema real. Importa para a patrulha, que depende da bateria.

## O que funcionou

- Imagem `physical-ai:jazzy` (ROS 2 Jazzy + simulador TurtleBot 4 + Xvfb), com cerca de 1,3 GiB de conteúdo. Dockerfile em `infra/docker/Dockerfile`.
- Simulação sem janela: robô criado, `/scan` e `/odom` com dados. No modo com GPU Intel, `diffdrive_controller` ativo e o robô respondeu a `/cmd_vel`.
- As 4 CPUs liberadas ficaram saturadas em todos os modos, mesmo com a GPU.

## O que NÃO funcionou (e por quê)

| Problema | Causa | Solução |
|---|---|---|
| Pacote `ros-jazzy-turtlebot4-tutorials` não existe | Os tutoriais (`turtlebot4_python_tutorials`, `turtlebot4_openai_tutorials`) não têm pacote apt para Jazzy. O PDF do colega cita um `apt install` que provavelmente vale só para Humble | Compilado do GitHub (`turtlebot/turtlebot4_tutorials`, branch `jazzy`). Já está na imagem |
| Gazebo abortava (`Couldn't open X display`) | Mesmo com `--headless-rendering`, o motor Ogre abre uma tela X para criar câmera e lidar | Tela virtual Xvfb |
| `xvfb-run` travava | Rodando como PID 1 no container, o sinal de pronto é ignorado | `docker run --init` e subir o Xvfb manualmente |
| `gz_args` ignorado | `sim.launch.py` do TurtleBot 4 monta o `gz_args` fixo, com GUI | Cópia modificada em `infra/docker/sim_headless.launch.py`, montada por cima do original |
| Simulação a 5% do tempo real | Xvfb renderiza a câmera e o lidar por CPU (llvmpipe) | Usar a GPU Intel: sobe para cerca de 18%, ainda longe do tempo real |
| Janela do Gazebo estoura 2,5 GiB | A interface gráfica soma memória ao servidor | Rodar sem janela, ou visualizar por outro meio |

## Simulador leve (`nav2_loopback_sim`), sem Gazebo

Nav2 real, sem física nem renderização. Base, bateria e resposta do AMCL são falsas (`infra/tools/fake_tb4_base.py`). Script: `infra/docker/treino_leve.sh`. Mapa `warehouse` do `turtlebot4_navigation`.

| O que foi medido | Resultado |
|---|---|
| RAM do container | Cerca de 500 MiB, ou 870 MiB com o processo do RViz (a janela não foi confirmada) |
| CPU | Cerca de 2 núcleos, mesmo com pouca atividade |
| `patrol_loop` sem alteração | Roda: inicializa, sai da base falsa, lê a bateria, manda destinos |
| Reação à bateria crítica | Funciona, encerrando o programa |
| Caminho de docking por bateria baixa | Nunca rodou em 5/nov. **Rodou em 9/nov**, com o resultado descrito na seção de atualização acima |
| Navegação | **Com falhas e causa desconhecida.** `(-5, 1)` falhou após 209 s e 14 erros `Failed to make progress`, com o robô parado perto de `(-0,5, 0)` e `/cmd_vel` em zero. Em outra execução, o trecho seguinte avançou cerca de 14 m em cerca de 3 minutos |

Causas descartadas: CPU (3 e 8 núcleos dão o mesmo resultado), obstáculo no mapa (área livre em volta), camada do `costmap` (testei a `StaticLayer` nos dois costmaps, como pede a documentação, e nada mudou). Parei de investigar por decisão de tempo. Não testei trocar o controlador MPPI por outro.

Defeitos do `patrol_loop` oficial achados na leitura e no teste: bateria sem valor inicial, bateria vista só entre destinos e resultado do destino ignorado. Detalhes em `estudo/semana-3-nav2-e-patrol.md`.

## Próximos passos possíveis

1. Usar o servidor do INF para a simulação e deixar o notebook só como cliente (premissa do mapa de estudo).
2. Só se o INF demorar: reduzir o custo dos sensores (taxa da câmera OAK-D e do lidar) num modelo customizado.

## Como rodar com segurança

`infra/docker/run_sim_headless.sh` (limite de 2,5 GiB de RAM sem swap e 4 CPUs, modo Xvfb). Parar: `docker rm -f tb4sim`.

Para o modo com GPU Intel, que é o mais rápido, rodar `xhost +SI:localuser:root` antes, trocar o Xvfb por `-e DISPLAY=:1 -v /tmp/.X11-unix:/tmp/.X11-unix:ro` e, ao final, rodar `xhost -SI:localuser:root`.

**Não rodar `docker build` com o `infra/docker/Dockerfile`:** ele não tem limite de memória. A imagem atual foi feita com `docker run --memory=2g` seguido de `docker commit`.

## Observação sobre o travamento do notebook

Causa provável, com evidência indireta: o `docker build` comum não tem limite de memória, e a pressão de memória e de disco registrada pelo kernel (`/proc/pressure`) estava alta logo depois da interrupção, com o navegador e o editor abertos. O log do kernel não mostrou evento de OOM. Desde então, toda instalação e simulação roda em container com teto de memória.

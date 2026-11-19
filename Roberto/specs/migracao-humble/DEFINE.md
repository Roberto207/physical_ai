# DEFINE: migração das imagens e da infra para ROS 2 Humble

**Status:** Aprovado em 2026-11-18 (portão da skill `/sdd`). Corrigido em 2026-11-18 pelo crítico EARS (primeira rodada): 23 dos 32 critérios foram reescritos ou divididos, e entraram SEG-04 a SEG-06, LCH-04, SIM-04b, SIM-06b e CFG-02b.
**Data:** 2026-11-18
**Decisões de base:** `docs/decisoes/ADR-001-ros2-humble.md` e `docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md`

## Resposta direta

Os requisitos abaixo dizem **o que** a migração precisa entregar, em frases testáveis (formato EARS). O **como** fica no `DESIGN.md`, que liga cada ID a uma verificação. A lógica da patrulha (`specs/patrol-inf/`) não muda. O que muda são as imagens, os compose, os scripts, as configurações que citam a distro e o lugar onde os nós ROS são compostos.

## Cenário (2026-11-18)

| Máquina | Papel | Distro |
|---|---|---|
| PC do laboratório (NUC14RVK-B) | Simula (Gazebo, L1 leve) e comanda o robô real | Humble em Docker (antes, Jazzy) |
| TurtleBot 4 do laboratório | Testes físicos (L4) | Humble, Ubuntu 22.04 (não muda) |
| Notebook do Roberto | Edita código e roda o L0 (pytest, sem Docker) | Nenhuma |

## Termos

| Termo | Significado |
|---|---|
| Imagem do projeto | Toda imagem `physical-ai:*` gerada pelo `infra/docker/Dockerfile` |
| Serviço | Um serviço de `infra/compose/sim.yaml` ou `infra/compose/robo.yaml` |
| Script de host | Arquivo `infra/docker/*.sh` que roda fora do container (o `entrypoint.sh` roda dentro e não conta) |
| Linha de código | Linha cujo primeiro caractere que não é espaço não é `#`. As outras são comentário |
| Distro da imagem | O valor da variável `ROS_DISTRO` gravada na imagem (`docker image inspect`). As imagens `ros:*` oficiais já definem essa variável |
| Base Jazzy | O commit apontado pela tag `jazzy-final` (PRE-01). "Hoje" e "de antes" nos requisitos querem dizer esse commit |
| Loopback vendorizado | Cópia do `nav2_loopback_sim` (ramo `jazzy` do navigation2) dentro do nosso workspace, adaptada ao Humble |
| `lab_tb4` | Pacote ROS novo (ament_python) com os launches de ambiente, a base falsa, o vigia e o conferidor do L1 |
| Os 11 cenários L1 | `ciclo l1b dock_falha queda_bateria sem_bateria fora_da_doca sem_servidor sem_relogio bateria_perdida falhas_seguidas sigint` |
| Comando de nó | `ros2 launch` ou `ros2 run`. Os comandos de CLI de uma só resposta (`ros2 topic list`, `ros2 service call`, `ros2 action send_goal`) não contam |

Os valores entre colchetes, como `[3]`, são padrões propostos.

## IMG: imagens

- **IMG-01** (Ubiquitous): Toda linha `FROM` do `infra/docker/Dockerfile` DEVE ser `ros:humble-ros-base` ou o nome de outro estágio do mesmo Dockerfile.
- **IMG-01b** (Ubiquitous): Todo pacote instalado por `apt-get install` no Dockerfile cujo nome comece com `ros-` DEVE começar com `ros-humble-`. A única exceção é `ros-dev-tools`, que não é de uma distro.
- **IMG-02** (Ubiquitous): O Dockerfile DEVE ter exatamente os alvos `base`, `robo`, `sim` e `llm`, e o `construir_imagem.sh` DEVE gerar exatamente as imagens `physical-ai:base`, `physical-ai:robo`, `physical-ai:sim` e `physical-ai:llm`.
- **IMG-03** (Ubiquitous): Toda imagem do projeto DEVE ter um entrypoint que carrega `/opt/ros/$ROS_DISTRO/setup.bash` e, quando o arquivo existir, `/opt/tb4_ws/install/setup.bash`, antes de executar o comando do serviço.
- **IMG-04** (Ubiquitous): Nenhuma linha de código de `infra/compose/*.yaml` ou dos scripts de host DEVE conter `jazzy` ou `humble`. As exceções são a constante `DISTRO_ESPERADA` do `lab.sh` (SEG-01) e a constante `DISTRO_ANTIGA` do `construir_imagem.sh` (PRE-02).
- **IMG-05** (Ubiquitous): Nenhuma imagem do projeto DEVE conter os pacotes `ros-humble-turtlesim`, `ros-humble-demo-nodes-py` e `x11-apps`.
- **IMG-06** (Unwanted): SE o `MemTotal` de `/proc/meminfo` for menor que `[12 GiB]` ENTÃO o `construir_imagem.sh` NÃO DEVE rodar `docker build` nem `docker tag`, e DEVE sair com o código 1. Essa conferência vem antes de qualquer outra ação do script.

## PRE: preservação do Jazzy

- **PRE-01** (Ubiquitous): O repositório DEVE ter a tag git anotada `jazzy-final`, no ramo `main`, apontando para o último commit em que todas as linhas `FROM` do `infra/docker/Dockerfile` partem de `ros:jazzy-ros-base` ou de um estágio interno.
- **PRE-02** (Event-driven): QUANDO o `construir_imagem.sh` for construir um alvo e já existir a imagem `physical-ai:<alvo>` com distro `jazzy` ENTÃO ele DEVE criar a tag `physical-ai:jazzy-<alvo>` para essa imagem antes do `docker build` desse alvo.
- **PRE-03** (Ubiquitous): O ADR-001 DEVE trazer os dois comandos de retorno: `git checkout jazzy-final` e `for a in base robo sim; do docker tag physical-ai:jazzy-$a physical-ai:$a; done`.

## SEG: segurança da rede do robô

- **SEG-01** (Unwanted): SE alguma imagem citada no `infra/compose/robo.yaml` tiver distro diferente de `humble`, ou não tiver a variável `ROS_DISTRO`, ENTÃO o `lab.sh robo` NÃO DEVE iniciar nenhum container, em nenhuma ação, e DEVE mostrar a imagem e a distro encontradas e sair com o código 1.
- **SEG-02** (Ubiquitous): No `robo.yaml` e no perfil do Nav2 que ele usa, NÃO DEVE existir `stamped:=true`, `-p stamped:=true` nem `enable_stamped_cmd_vel: true`. Assim nenhum serviço publica `TwistStamped` em `cmd_vel`, `cmd_vel_nav` ou `cmd_vel_smoothed`.
- **SEG-03** (Ubiquitous): Todo serviço do `robo.yaml` DEVE ter a chave `profiles`.
- **SEG-04** (Event-driven): QUANDO o serviço `teleop` ou `patrulha` do `robo.yaml` iniciar ENTÃO ele DEVE pedir que se digite `SIM` e DEVE encerrar sem executar comando de nó se a resposta for outra.
- **SEG-05** (Ubiquitous): No comando do serviço `patrulha` (sim e robo), o `ros2 launch patrulha_tb4` DEVE vir depois de um `validar_pontos` encadeado de forma que uma saída diferente de 0 impeça o launch.
- **SEG-06** (Ubiquitous): Nenhum serviço do `robo.yaml` DEVE enviar goals de dock ou undock por conta própria, nem mudar rede ou configuração do robô. O nó da patrulha faz dock e undock como parte dos requisitos PAT da `patrol-inf`, e isso não é exceção a esta regra: é o comportamento especificado lá.

## LCH: launches e scripts

- **LCH-01** (Ubiquitous): Os launches `gazebo.launch.py`, `sim_leve.launch.py` e `l1.launch.py` DEVEM existir em `lab_tb4/launch/` e ser instalados pelo `setup.py` do `lab_tb4`.
- **LCH-04** (Ubiquitous): O `patrulha.launch.py` DEVE declarar somente o nó `patrulha` e o handler de encerramento dele, como hoje (AMB-01 da `patrol-inf`).
- **LCH-02** (Ubiquitous): Nenhuma linha de código dos scripts de host DEVE conter um comando de nó junto de `&`, `nohup`, `setsid` ou `docker run -d`. Cada `docker run`, `docker exec` e `docker compose run|exec` DEVE executar no máximo um comando de nó.
- **LCH-03** (Ubiquitous): A base falsa DEVE rodar com `ros2 run lab_tb4 base_falsa` e declarar os mesmos 11 parâmetros, com os mesmos nomes e valores padrão, do `infra/tools/fake_tb4_base.py` da base Jazzy.

## SIM: simuladores

- **SIM-01** (Event-driven): QUANDO o serviço `gazebo` do `sim.yaml` estiver em execução há `[90 s]` de relógio ENTÃO cada um dos tópicos `/scan`, `/odom`, `/tf` e `/dock_status` DEVE ter entregue pelo menos 1 mensagem, no mundo do argumento `world` (padrão `maze`).
- **SIM-01b** (Ubiquitous): O serviço `gazebo` NÃO DEVE iniciar a interface gráfica do Gazebo (processo `ign gazebo -g` ou o cliente de GUI).
- **SIM-01c** (Event-driven): QUANDO o serviço `gazebo` tiver avançado `[60 s]` de tempo simulado (tópico `/clock`) ENTÃO o `/battery_state` DEVE ter entregue pelo menos 1 mensagem.
- **SIM-02** (Ubiquitous): Os serviços `slam`, `localizacao`, `nav2`, `rviz`, `teleop` e `patrulha` DEVEM existir com o mesmo nome no `sim.yaml` e no `robo.yaml`.
- **SIM-02b** (Ubiquitous): Entre os dois arquivos, cada um desses serviços SÓ PODE diferir em: imagem, `mem_limit`/`memswap_limit`, rede (`network_mode`, `ipc`, `env_file`, `ROS_DOMAIN_ID`), `use_sim_time`, `namespace`, `params_file`, a confirmação `SIM` e o `CONFIG` padrão.
- **SIM-03** (Event-driven): QUANDO o `sim_leve.launch.py` for iniciado ENTÃO, em até `[60 s]` de relógio, o `map_server` e os servidores de navegação do Nav2 DEVEM estar no estado de lifecycle `active`, o loopback DEVE publicar `/odom` e `/tf`, e a base falsa DEVE publicar `/battery_state`.
- **SIM-03b** (Optional): ONDE o argumento `rviz:=true` for passado ao `sim_leve.launch.py`, o launch DEVE iniciar o `rviz2`. Sem esse argumento, ou com `rviz:=false`, NÃO DEVE existir processo `rviz2`.
- **SIM-04** (Event-driven): QUANDO o `teste_l1.sh` receber um dos 11 nomes de cenário ENTÃO ele DEVE rodar o cenário até o veredito. QUANDO receber outro nome ENTÃO DEVE listar os 11 nomes e sair sem iniciar container.
- **SIM-04b** (Ubiquitous): Os parâmetros de cada cenário DEVEM vir de `lab_tb4/config/cenarios_l1.yaml`, com os campos `config`, `base`, `limite_s`, `subir_nav2`, `subir_base`, `nav2_extra`, `patrulha_extra` e `sinal_no_fim`, e com os mesmos valores do `case` do `teste_l1.sh` da base Jazzy.
- **SIM-05** (Event-driven): QUANDO o container de um cenário encerrar, por qualquer motivo (fim normal, tempo-limite, OOM ou retentativas esgotadas), ENTÃO DEVE existir a pasta `progresso/evidencias/l1/AAAA-MM-DD_HH-MM-SS-<cenario>/` com `execucao.txt`, `container.log`, `docker_stats.csv` e `veredito.txt`. O `veredito.txt` é a saída do `conferir_l1`. Os arquivos `*.jsonl`, `nav2.log`, `base_falsa.log`, `patrulha.log` e `ambiente.txt` também DEVEM estar lá sempre que o container chegou a produzi-los.
- **SIM-06** (Unwanted): SE o `nav2.log` contiver `Aborting bringup` nos primeiros `[15 s]` depois do início do Nav2 leve ENTÃO o `teste_l1.sh` DEVE rodar o cenário de novo num container novo, até `[3]` tentativas no total, e acrescentar a linha `tentativa <N>: Aborting bringup` ao `nav2_tentativas.txt` da pasta de evidências.
- **SIM-06b** (Unwanted): SE as `[3]` tentativas do SIM-06 falharem ENTÃO o `veredito.txt` DEVE dizer `REPROVADO` com o motivo `nav2_nao_subiu`.
- **SIM-07** (Ubiquitous): O loopback vendorizado DEVE ficar em `workspace/meu_ws/src/terceiros/nav2_loopback_sim/`, com o `LICENSE` original e um `ORIGEM.md` com a URL, o SHA do commit copiado e a lista de patches aplicados.

## CFG: configurações

- **CFG-01** (Event-driven): QUANDO o campo `mapa` da configuração começar com `pkg://` ENTÃO o `config.carregar` DEVE resolver `pkg://<pacote>/<caminho>` como `<share do pacote>/<caminho>`, pelo ament_index.
- **CFG-02** (Unwanted): SE o ament_index não encontrar o pacote de um `mapa` com `pkg://` ENTÃO o `config.carregar` DEVE levantar `ConfigInvalida` com o motivo `mapa_pacote_inexistente`, e o nó da patrulha DEVE gravar `config_invalida` no log JSONL e sair com o código de saída 2.
- **CFG-02b** (Unwanted): SE o `ament_index_python` não estiver instalado e o `mapa` começar com `pkg://` ENTÃO o `config.carregar` DEVE levantar `ConfigInvalida` com o motivo `pkg_sem_ros`.
- **CFG-03** (Ubiquitous): Nenhuma linha de código das configurações em `patrulha_tb4/config/` DEVE conter `/opt/ros/`.
- **CFG-04** (Ubiquitous): Ignorando as linhas de comentário, o `nav2_inf_devagar.yaml` DEVE ser igual ao `config/nav2.yaml` do `ros-humble-turtlebot4-navigation`, exceto no `velocity_smoother`: o primeiro valor de `max_velocity` DEVE ser `0.15` e o de `min_velocity`, `-0.15`. O comentário de cabeçalho DEVE citar a versão do pacote de origem.
- **CFG-05** (Ubiquitous): A migração NÃO DEVE alterar o `decisao.py`. Os testes de `patrulha_tb4/test/` da base Jazzy DEVEM passar sem edição. A única exceção é o `test_config.py`, que pode ganhar testes do CFG-01, do CFG-02 e do CFG-02b.

## CI

- **CI-01** (Ubiquitous): A matriz do job `l0` do `.github/workflows/ci.yml` DEVE ter somente `humble`.

## DOC: documentação

- **DOC-01** (Event-driven): QUANDO o documento da F1 em `docs/tarefas/` registrar a V5 como aprovada pelo Roberto ENTÃO o `grep -niE 'não use o .?lab\.sh robo'` DEVE voltar vazio em `como_rodar.md`, `specs/patrol-inf/kit-de-campo.md`, `infra/compose/robo.yaml` e `contexto/pendencias.md`.
- **DOC-02** (Ubiquitous): Todo comando em bloco de código do `como_rodar.md` e do `kit-de-campo.md` que comece com `./lab.sh` DEVE usar uma ação listada no `uso` do `lab.sh`, e todo `ros2 launch <pacote> <arquivo>` citado DEVE passar no `--show-args` dentro da imagem `physical-ai:sim`.
- **DOC-03** (Ubiquitous): O `specs/patrol-inf/DESIGN.md` DEVE ganhar um adendo com os níveis L0 (pytest), L1 (leve vendorizado), L3 (Gazebo no PC do lab, o principal) e L4 (robô), e com o plano da medição M-GZH. O resultado da M-GZH só entra se ela for rodada a pedido do Roberto.
- **DOC-04** (Ubiquitous): Cada fase da implementação (F0 a F4 do DESIGN) DEVE fechar com um documento em `docs/tarefas/` e uma entrada em `docs/registro-de-mudancas.md`.

## DEVE / NÃO DEVE (resumo)

| DEVE | NÃO DEVE |
|---|---|
| Imagens só Humble, quatro alvos, entrypoint sem distro escrita | Rodar qualquer imagem Jazzy na rede do robô |
| Jazzy recuperável pela tag `jazzy-final` e pelas imagens `jazzy-<alvo>` | Apagar as imagens Jazzy do PC |
| Composição de nós em `launch.py` no `lab_tb4` | Mudar a lógica da patrulha (`decisao.py`) |
| Gazebo Fortress como simulador principal, e o L1 leve mantido | Rodar a medição M-GZH sem pedido explícito do Roberto |
| Os 11 cenários L1 com o mesmo veredito | Mudar rede, firmware, distro ou configuração do robô |
| Pedir permissão e citar a documentação oficial antes de tocar o robô (V5) | Fazer o enxugamento dos documentos aqui (tem spec própria: `specs/enxugamento/PREVIA.md`) |

## Fora do escopo

- O provedor de LLM (pendência aberta). O alvo `llm` só troca de distro.
- O CI das Fases B a F (imagem no runner, L1 noturno).
- A limpeza dos documentos e do contexto, exceto o que a migração remove.

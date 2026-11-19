# Como rodar

Desde 2026-11-18, tudo roda em **ROS 2 Humble**, a mesma distro do robô do laboratório (ADR-001, `docs/decisoes/`). O **PC do laboratório simula** e comanda o robô. O **notebook** só edita código e roda os testes L0. A versão Jazzy está na tag git `jazzy-final`.

Os caminhos abaixo partem da raiz do repositório. No notebook ela fica em `~/dev/physical_ai`; no PC do lab, em `~/physical_ai`.

| Quero | Seção |
|---|---|
| Rodar os testes da lógica | 1 |
| Construir as imagens | 2 |
| Subir o Gazebo e fazer um mapa no simulador | 3 |
| Rodar os 11 cenários de falha no simulador leve | 4 |
| **Rodar a patrulha (patrol_loop) no simulador** | **5** |
| Fazer o mapa do laboratório com o robô real | 6 |
| **Rodar a patrulha (patrol_loop) no robô real** | **7** |

## 1. Testes da lógica (L0): notebook ou PC, sem ROS e sem Docker

```bash
cd workspace/meu_ws/src/patrulha_tb4
python3 -m pytest -q                  # 155 testes, menos de 1 s
python3 test/checar_rastreio.py       # todo requisito L0 da spec patrol-inf tem teste?
cd ../lab_tb4 && python3 -m pytest -q # 17 testes: cenários do L1 e conferidor
```

Conferir uma configuração contra o mapa, antes de o robô andar (só dentro de um container, por causa do `pkg://`):

```bash
infra/docker/lab.sh sim compose run --rm -e COMPILAR_WS=patrulha_tb4 ferramentas \
  validar_pontos /workspace/meu_ws/src/patrulha_tb4/config/leve_reduzido.yaml
```

## 2. Imagens (só no PC do laboratório)

```bash
infra/docker/construir_imagem.sh base robo sim   # recusa com menos de 12 GiB de RAM (o notebook)
docker images 'physical-ai'                      # as Jazzy antigas ficam como physical-ai:jazzy-<alvo>
```

Construa `base` e `robo` juntas. Se só a `robo` for construída, a `base` continua Jazzy, e o `lab.sh robo` recusa (SEG-01).

## 3. Simulação no PC: Gazebo, o simulador principal (ADR-002)

Rede isolada e domínio 42: não alcança o robô real. Esta seção é o treino do **mapa**. Para a patrulha, veja a seção 5.

```bash
infra/docker/lab.sh sim subir gazebo slam rviz   # espere cerca de 1 min (./lab.sh sim logs gazebo)
infra/docker/lab.sh sim undock                   # tira o robô simulado da doca
infra/docker/lab.sh sim teleop                   # dirige pelo teclado, a 0,15 m/s
infra/docker/lab.sh sim salvar teste_maze        # grava em workspace/mapas/ e confere
infra/docker/lab.sh sim parar
```

`MUNDO=depot infra/docker/lab.sh sim subir gazebo` troca o mundo (`maze` é o padrão).

## 4. Simulador leve e os 11 cenários L1 (no PC)

Os cenários de falha (dock que falha, bateria que cai, servidor ausente) rodam no simulador leve: o `nav2_loopback_sim` vendorizado e a base falsa.

```bash
infra/docker/teste_l1.sh lista            # os 11 cenários
infra/docker/teste_l1.sh ciclo            # ciclo de recarga completo
infra/docker/teste_l1.sh dock_falha       # o dock falha 1 vez e a patrulha tenta de novo
```

Cada execução deixa uma pasta em `workspace/logs/l1/` com o log JSONL, os logs do Nav2, da base falsa e da patrulha, e o veredito (APROVADO ou REPROVADO). Os parâmetros de cada cenário estão em `workspace/meu_ws/src/lab_tb4/config/cenarios_l1.yaml`.

O leve à mão, sem cenário: `infra/docker/lab.sh sim subir leve` (não junto com o `gazebo`).

## 5. Patrulha (patrol_loop) no simulador: modo `sim`

O nó `patrulha` (pacote `patrulha_tb4`) anda entre os pontos do arquivo de configuração, vigia a bateria, volta à doca para carregar e sai de novo, sem parar. No modo `sim`, o mundo, a bateria, a doca e o AMCL vêm do Gazebo (a Create 3 simulada). A rede é isolada e o domínio é o 42: nada disso alcança o robô real. O `sim` não pede `SIM` antes de andar.

### 5.1 Antes de começar

| O que | Como conferir |
|---|---|
| Imagem `physical-ai:sim` | `docker images 'physical-ai'` (seção 2) |
| Mapa do mundo | O `maze` do pacote `turtlebot4_navigation` serve sem fazer nada. Um mapa seu fica em `workspace/mapas/` e aparece como `/mapas/` dentro do container |
| Configuração | O padrão é `workspace/meu_ws/src/patrulha_tb4/config/gazebo_maze.yaml` (pontos curtos do `maze`, bateria relativa) |
| Nada rodando antes | `infra/docker/lab.sh sim estado`. Se houver algo de uma sessão anterior, `infra/docker/lab.sh sim parar` |

### 5.2 Passo a passo (um terminal por passo)

**Terminal 1: o mundo, a localização e o Nav2**

```bash
infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz
infra/docker/lab.sh sim logs gazebo       # espere cerca de 1 min até o Gazebo estar pronto
infra/docker/lab.sh sim logs nav2         # confira que o Nav2 terminou de subir
```

- O robô simulado nasce **na doca**. **Não rode `undock` antes:** a patrulha só começa na doca (se não, sai com o código 6) e ela mesma faz o undock. Se você acabou de mapear, rode `infra/docker/lab.sh sim parar` e suba tudo de novo para o robô voltar à doca.
- **Não suba o `slam` junto.** SLAM e localização publicam a mesma transformação `map → odom`.
- Outro mapa: `MAPA=/mapas/teste_maze.yaml infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz`. O campo `mapa` da configuração tem de ser o mesmo mapa.

**Terminal 2: a patrulha (fica na frente, com o log na tela)**

```bash
infra/docker/lab.sh sim patrulha                                     # configuração padrão (gazebo_maze.yaml)
CONFIG=/mapas/minha_config.yaml infra/docker/lab.sh sim patrulha     # outra configuração, em workspace/mapas/
```

O serviço compila o pacote (cerca de 1 s), roda o `validar_pontos` (recusa configuração inválida, sem andar) e só então sobe o nó.

### 5.3 O que a patrulha faz sozinha

| Situação | O que acontece |
|---|---|
| Início, na doca, bateria acima de `alta` | Undock e começa os pontos, na ordem |
| Bateria abaixo de `baixa` (ou `critica`, ou sem leitura) | Cancela o destino, vai à aproximação da doca, encaixa e carrega |
| Bateria de volta a `alta` | Undock e retoma **o mesmo ponto** que estava em andamento |
| Três destinos falhos seguidos | Vai à doca, encaixa e encerra com o código 7 |
| Dock não confirmado | Tenta de novo, até o limite (`tentativas_dock`); depois encerra com o código 4 |

### 5.4 Acompanhar

- O terminal da patrulha mostra cada evento, no formato `[fase] evento detalhes`.
- O log fica em `workspace/logs/`, um arquivo `AAAA-MM-DD_HH-MM-SS.jsonl` por execução, com um evento por linha e o `resumo` no fim.
- `infra/docker/lab.sh sim estado` lista o que está rodando, e `infra/docker/lab.sh sim logs <serviço>` mostra as últimas linhas de um serviço.

### 5.5 Mandar o robô de volta à doca (go to dock)

Em **outro terminal**, com a patrulha rodando:

```bash
infra/docker/lab.sh sim voltar-doca
```

O comando chama o serviço `/patrulha/voltar_doca` (PAT-23). A resposta `success=True` só diz que o pedido chegou. Depois disso, a patrulha cancela o destino (sem contar como falha), vai à aproximação da doca, faz o dock e **encerra com o código 0**, sem carregar nem retomar a ronda. No log aparecem `doca_pedida`, `dock_ok` e `encerrado` (com o detalhe `voltar_doca`).

- Se a patrulha não estiver rodando, o comando espera 30 s e avisa que não houve resposta.
- **Não envie `dock` por fora da patrulha** (`ros2 action send_goal ... /dock`): ela não enxerga esse dock, e a Create 3 recusa o dock se já estiver encaixada.
- O pedido também vale com o robô já encaixado (encerra na hora) e durante a ida à doca por bateria (passa a encerrar em vez de carregar).

### 5.6 Parar

| Quero | Faça |
|---|---|
| Parar onde o robô está, sem ir à doca | Ctrl+C no terminal da patrulha. Ela cancela a ação e sai com o código 0 |
| Encerrar com o robô encaixado | `infra/docker/lab.sh sim voltar-doca` (seção 5.5) |
| Desligar o simulador | `infra/docker/lab.sh sim parar` (derruba os containers e devolve a posse de `workspace/mapas/` e `workspace/logs/`) |

Depois de um Ctrl+C no meio da ronda, o robô pode não estar na doca. Para rodar de novo, reinicie o mundo (`parar` e `subir`).

### 5.7 Se a patrulha sair logo (código de saída)

| Código | Motivo | O que olhar |
|---|---|---|
| 2 | Configuração ou pose inválida | A mensagem do `validar_pontos`: pose fora do mapa, em célula ocupada ou perto de obstáculo |
| 3 | Sem leitura de `/battery_state` | O `gazebo` está de pé? A bateria simulada demora a sair |
| 4 | Dock falhou em todas as tentativas | A `aproximacao_doca` do arquivo (de frente para a doca, perto dela) |
| 5 | Undock falhou | Os logs do `gazebo` |
| 6 | Começou fora da doca | Reinicie o mundo (`parar` e `subir`) |
| 7 | Três destinos falhos seguidos | Os pontos e o mapa; os logs do `nav2` |
| 8 | Servidor de ação não respondeu em 30 s | O Nav2 ainda subindo; espere e rode de novo |
| 9 | Sem `/clock` | O `gazebo` está rodando? |
| 0 | Encerramento pedido (Ctrl+C) ou `voltar-doca` | Normal |

**Não verificado:** a sequência 5.2 a 5.5 ainda não foi rodada no Gazebo do PC do laboratório (depende da V1 e da fumaça do Gazebo). O `voltar-doca` só foi testado na lógica (L0), não no ROS. Veja `docs/tarefas/2026-11-19-voltar-doca.md`.

## 6. Robô real (no PC): rede e mapa

**ATENÇÃO (2026-11-16):** não use o `lab.sh robo` até a imagem Humble ser verificada com o robô (V5 de `specs/migracao-humble/DESIGN.md`). Nós Jazzy derrubaram o robô, que é Humble. As imagens agora são Humble, e o `lab.sh` recusa imagem de outra distro, mas o teste com o robô ainda não foi feito.

Mapa no robô real, só depois das etapas 1 a 3 do kit de campo (`specs/patrol-inf/kit-de-campo.md`):

```bash
infra/docker/lab.sh robo checar-rede      # só lê: rotas, e /robot1/scan, /robot1/tf e /robot1/odom chegam?
infra/docker/lab.sh robo subir slam rviz  # confere a rede e sobe (não move o robô)
infra/docker/lab.sh robo teleop           # move o robô REAL: pede que você digite SIM
infra/docker/lab.sh robo salvar lab
infra/docker/lab.sh robo parar
```

- O que está rodando: `infra/docker/lab.sh robo estado`.
- Conferir um mapa: `infra/docker/lab.sh conferir workspace/mapas/lab.yaml`.
- O robô do lab é Humble, usa Discovery Server e o namespace `/robot1` (`ROBO_NS` muda; `ROBO_NS=` para nenhum).
- O PC precisa de rotas pelo robô para `192.168.186.0/24` e `192.168.185.0/24`: o `checar-rede` mostra o comando.
- Acesso ao robô por cabo e por Wi-Fi: `docs/guias/acesso-ao-robo.md`. A rede do PC fica em `infra/lab/rede_lab.env`.

## 7. Patrulha (patrol_loop) no robô real: modo `robo`

A patrulha é a mesma da seção 5; muda o que responde do outro lado. No modo `robo`, a bateria, a doca e os sensores são do TurtleBot 4 físico, e o PC fala com ele pela rede do laboratório (Discovery Server, domínio do `infra/lab/rede_lab.env`, namespace `/robot1`). **O robô anda sozinho:** a patrulha e o `voltar-doca` pedem que você digite `SIM`.

### 7.1 Antes de começar (todos os itens)

| # | O que | Como conferir |
|---|---|---|
| 1 | A V5 passou e o Roberto liberou o robô | O aviso da seção 6 só sai depois disso |
| 2 | Uma pessoa de segurança ao lado, com a área livre | Protocolo do kit de campo (`specs/patrol-inf/kit-de-campo.md`) |
| 3 | O robô **na doca** | A patrulha encerra com o código 6 se não estiver |
| 4 | A rede está boa | `infra/docker/lab.sh robo checar-rede` termina com `REDE OK` |
| 5 | Um mapa utilizável do laboratório | `infra/docker/lab.sh conferir workspace/mapas/lab.yaml` diz `UTILIZÁVEL` |
| 6 | Uma configuração preenchida | Copie `workspace/meu_ws/src/patrulha_tb4/config/inf_lab.yaml` para a pasta `workspace/mapas/` com outro nome (por exemplo, `inf_lab_preenchido.yaml`) e preencha `mapa`, `pose_inicial`, `aproximacao_doca`, `pontos` e o `bateria_perdida_s` medido (kit de campo, etapas 1 e 6) |
| 7 | A configuração aprovada pelo `validar_pontos` | O serviço da patrulha roda o `validar_pontos` antes de pedir o `SIM`, mas rode antes à mão para ver o erro cedo (seção 1) |

O Nav2 do `robo` usa por padrão o perfil de velocidade reduzida (`nav2_inf_devagar.yaml`, 0,15 m/s).

### 7.2 Passo a passo (um terminal por passo)

**Terminal 1: localização e Nav2 (não movem o robô)**

```bash
infra/docker/lab.sh robo checar-rede
MAPA=/mapas/lab.yaml infra/docker/lab.sh robo subir localizacao nav2 rviz
infra/docker/lab.sh robo logs nav2        # confira que o Nav2 terminou de subir
```

Não suba o `slam` junto da localização. A pose inicial da `pose_inicial` é publicada pelo próprio nó da patrulha: você não precisa marcar o "2D Pose Estimate" no RViz.

**Terminal 2: a patrulha (move o robô)**

```bash
CONFIG=/mapas/inf_lab_preenchido.yaml infra/docker/lab.sh robo patrulha
```

O serviço roda o `validar_pontos`, mostra o aviso ("o robô REAL vai andar sozinho") e espera que você digite `SIM`. Qualquer outra resposta cancela. O `CONFIG` é o caminho **dentro do container**: `workspace/mapas/` aparece como `/mapas/`.

Antes da patrulha completa, o kit de campo manda testar com 1 ponto perto da doca (etapas 5 a 7).

### 7.3 Mandar o robô de volta à doca (go to dock)

Em **outro terminal**, com a pessoa de segurança ao lado:

```bash
infra/docker/lab.sh robo voltar-doca
```

O comando mostra o aviso, pede `SIM` e chama o serviço `/robot1/patrulha/voltar_doca` (o namespace vem do `ROBO_NS`). A patrulha cancela o destino, vai à aproximação da doca, encaixa e encerra com o código 0, sem carregar nem retomar. O significado da resposta e os cuidados são os da seção 5.5: sem resposta em 30 s, o comando avisa que a patrulha não está rodando.

Não envie `dock` à mão com a patrulha rodando, pelo mesmo motivo da seção 5.5.

### 7.4 Parar

| Quero | Faça |
|---|---|
| Parar o robô já | A pessoa de segurança, no robô (o software não garante parada imediata) |
| Parar a patrulha onde o robô está | Ctrl+C no terminal da patrulha |
| Encerrar com o robô encaixado | `infra/docker/lab.sh robo voltar-doca` |
| Desligar tudo | `infra/docker/lab.sh robo parar` |

Os códigos de saída são os da tabela da seção 5.7. O log JSONL de cada execução fica em `workspace/logs/`.

**Não verificado:** nada da seção 7 rodou no robô real. Depende da V5 e da permissão do Roberto (`docs/tarefas/2026-11-18-f4-limpeza.md`, seção 4, item 7).

## Onde está a explicação

| Assunto | Arquivo |
|---|---|
| A migração para Humble (requisitos, design, fases) | `specs/migracao-humble/` e `docs/tarefas/2026-11-18-f*.md` |
| A patrulha (requisitos e testes) | `specs/patrol-inf/` |
| O pedido de retorno à doca (`voltar-doca`) | `docs/tarefas/2026-11-19-voltar-doca.md` |
| O que mudou e quando | `docs/tarefas/README.md` (e `docs/historico/registro-de-mudancas.md` até 2026-11-16) |

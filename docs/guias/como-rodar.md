# Como rodar

> **Outro robô:** os exemplos usam o `robot1`. Para outro, rode antes `infra/docker/lab.sh robo usar <nome>` e, nos comandos digitados, troque `/robot1` e o IP pelos dele (`docs/guias/acesso-ao-robo.md`, seção "Vários robôs").

Tudo roda em **ROS 2 Humble**, a mesma distro do robô (ADR-001, `docs/decisoes/`). O **PC do laboratório** simula e comanda o robô. O **notebook** só edita código e roda os testes sem ROS. A versão Jazzy está na tag git `jazzy-final`.

Os caminhos partem da raiz do repositório (`~/physical_ai` no PC do lab, `~/dev/physical_ai` no notebook).

## Qual guia usar

| Quero | Guia |
|---|---|
| **Patrulha no robô, ida e volta, terminando na doca** | `docs/guias/patrulha-volta-a-doca.md` |
| **Patrulha no robô em loop contínuo** | `docs/guias/patrulha-loop-continuo.md` |
| Lembrar um comando (rede, logs, sensores, subir, descer) | `docs/guias/comandos-basicos.md` |
| Entrar no robô, rede e rotas | `docs/guias/acesso-ao-robo.md` |
| **Linguagem natural (LLM): ensaiar e rodar no robô** | `docs/guias/llm-linguagem-natural.md` |
| O que está em aberto | `docs/contexto/pendencias.md` |
| Testes, imagens, simulador, mapa e a patrulha `patrulha_tb4` | este arquivo |

## Onde estamos (25/11/2026)

- **Programas em uso no robô:** os de `workspace/patrulha_oficial/`, adaptados do exemplo oficial do TurtleBot 4, no mapa `workspace/mapas/mapa_lab_novo.yaml`.
- **Ensaiado:** o `patrol_loop.py` (via `rodar.sh 1`) já completou os quatro pontos uma vez; naquela execução a volta à doca falhou. Em 23/11 houve novas falhas no ponto 1, sem causa determinada (`docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`).
- **Sem registro de ensaio físico:** `patrol_loop2.py` e `loop.py`.
- **LLM:** o nó `llm_tb4` interpreta e executa pedidos; o freio vem ligado. Execução ensaiada só com robô falso.
- **Patrulha anterior (`patrulha_tb4`):** não é a usada hoje no robô. O pacote continua necessário (seção 6).

## 1. Testes da lógica (sem ROS e sem Docker)

Precisam do `pytest`, que o `python3` do PC do lab não tinha em 25/11: rodar no notebook (o CI também roda).

```bash
(cd workspace/meu_ws/src/patrulha_tb4 && python3 -m pytest -q)                 # lógica da patrulha_tb4 e conferidor de mapa
(cd workspace/meu_ws/src/patrulha_tb4 && python3 test/checar_rastreio.py)      # todo requisito da spec patrol-inf tem teste?
(cd workspace/meu_ws/src/lab_tb4 && python3 -m pytest -q)                      # cenários do simulador leve
python3 infra/ferramentas/checar_caminhos.py                                   # caminhos citados nos documentos existem?
```

## 2. Imagens (só no PC do laboratório)

```bash
infra/docker/construir_imagem.sh base robo sim    # recusa com menos de 12 GiB de RAM
docker images 'physical-ai'                       # lista as imagens
```

Construa `base` e `robo` juntas: o `lab.sh robo` recusa qualquer imagem que não seja Humble.

## 3. Simulador (não alcança o robô real)

Rede isolada, domínio 42. Os modos `sim` e `robo` não rodam juntos.

### 3.1 Fazer um mapa no Gazebo

```bash
infra/docker/lab.sh sim subir gazebo slam rviz    # espere cerca de 1 min (lab.sh sim logs gazebo)
infra/docker/lab.sh sim undock                    # tira o robô simulado da doca
infra/docker/lab.sh sim teleop                    # dirige pelo teclado
infra/docker/lab.sh sim salvar teste_maze         # grava em workspace/mapas/ e confere
infra/docker/lab.sh sim parar
```

`MUNDO=depot` antes do comando de subir troca o mundo (`maze` é o padrão).

### 3.2 Cenários de falha no simulador leve

```bash
infra/docker/teste_l1.sh lista                    # cenários disponíveis
infra/docker/teste_l1.sh ciclo                    # ciclo de recarga completo
infra/docker/teste_l1.sh dock_falha               # o dock falha uma vez e a patrulha tenta de novo
```

Resultados em `workspace/logs/l1/`. Parâmetros em `workspace/meu_ws/src/lab_tb4/config/cenarios_l1.yaml`.

### 3.3 Patrulha `patrulha_tb4` no Gazebo

```bash
infra/docker/lab.sh sim parar                                  # mundo limpo, robô na doca
infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz     # sem slam junto
infra/docker/lab.sh sim logs nav2                              # espere o Nav2 subir
infra/docker/lab.sh sim patrulha                               # usa gazebo_maze.yaml; CONFIG=/mapas/x.yaml troca
infra/docker/lab.sh sim voltar-doca                            # em outro terminal: volta à doca e encerra
infra/docker/lab.sh sim parar
```

Não faça `undock` antes: a patrulha exige começar na doca. A sequência no Gazebo não tem registro de execução.

## 4. Mapa no robô real

```bash
infra/docker/lab.sh robo checar-rede              # só lê; precisa dizer REDE OK
infra/docker/lab.sh robo subir slam rviz          # mapeia (não move o robô); começar com ele na doca
infra/docker/lab.sh robo teleop                   # MOVE O ROBÔ: pede SIM
infra/docker/lab.sh robo salvar nome_do_mapa      # grava em workspace/mapas/ e confere
infra/docker/lab.sh robo parar                    # derruba tudo
```

Mapa atual: `workspace/mapas/mapa_lab_novo.yaml`. Cerca de 59,8% dele é área não mapeada: escolha destinos só em área livre.

## 5. Medir coordenadas no mapa

Com a localização e o RViz no ar, escute os cliques e use **Publish Point** no mapa:

```bash
infra/docker/lab.sh robo compose exec -T rviz bash -lc \
    'source /opt/ros/humble/setup.bash; ros2 topic echo /robot1/clicked_point geometry_msgs/msg/PointStamped'
```

Anote `point.x` e `point.y`. A ferramenta não fornece orientação, e a rotação da câmera do RViz faz "direita" e "cima" da tela não serem os eixos x e y. Os programas de `workspace/patrulha_oficial/` calculam a orientação pela direção do ponto seguinte.

## 6. Patrulha `patrulha_tb4` (programa anterior)

Nó próprio da equipe, em `workspace/meu_ws/src/patrulha_tb4`: lê um arquivo de configuração, anda pelos pontos, volta à doca com bateria baixa, carrega e sai de novo. Quem decide é o `decisao.py`; o `no_patrulha.py` liga a decisão ao ROS.

**O pacote não pode ser apagado inteiro:** os serviços `localizacao` e `nav2` do robô usam os parâmetros e o launch dele, e o `lab.sh conferir` usa o conferidor de mapa dele.

### 6.1 Configuração

Copie `workspace/meu_ws/src/patrulha_tb4/config/inf_lab.yaml` para `workspace/mapas/` e preencha `mapa` (caminho relativo ao arquivo), `pose_inicial`, `aproximacao_doca` (de frente para a doca, de 0,5 a 1 m) e `pontos`. Exemplo preenchido: `workspace/mapas/patrulha_mapa_lab_novo.yaml`. Valide antes de qualquer movimento:

```bash
PYTHONPATH=workspace/meu_ws/src/patrulha_tb4 python3 -m patrulha_tb4.pontos workspace/mapas/patrulha_mapa_lab_novo.yaml
```

Precisa dizer `APROVADA`. A validação confere ocupação e margem de 0,25 m, não a rota.

### 6.2 No robô real

```bash
infra/docker/lab.sh robo checar-rede
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2 rviz
CONFIG=/mapas/patrulha_mapa_lab_novo.yaml infra/docker/lab.sh robo patrulha    # MOVE O ROBÔ: pede SIM
infra/docker/lab.sh robo voltar-doca                                           # outro terminal; MOVE O ROBÔ: pede SIM
infra/docker/lab.sh robo parar
```

Robô na doca e pessoa ao lado. Este programa **publica a própria `pose_inicial`**, sobrescrevendo uma marcação diferente feita no RViz. Não envie `dock` à mão enquanto ele roda. `Ctrl+C` para a patrulha onde o robô está. Nos ensaios de 21/11 o Nav2 abortou os destinos.

### 6.3 Códigos de saída

| Código | Significado | Onde olhar |
|---|---|---|
| 0 | Encerrado (`Ctrl+C` ou `voltar-doca`) | log `resumo` |
| 2 | Configuração ou pose inválida | mensagem do `validar_pontos` |
| 3 | Sem leitura de bateria | tópico `battery_state` |
| 4 | Dock falhou em todas as tentativas | `aproximacao_doca`, `dock_status` |
| 5 | Undock falhou | doca energizada, robô encaixado |
| 6 | Começou fora da doca | encaixar o robô |
| 7 | Três destinos falhos seguidos | logs do `nav2` e da `localizacao` |
| 8 | Servidor de ação indisponível | Nav2 não subiu |
| 9 | Sem relógio (`/clock`) | Gazebo (sim) ou `use_sim_time` (real) |

Um log JSONL por execução fica em `workspace/logs/`.

## Onde está a explicação

| Assunto | Arquivo |
|---|---|
| Migração para Humble | `specs/migracao-humble/` |
| Requisitos e testes da `patrulha_tb4` | `specs/patrol-inf/` |
| Retorno à doca sob demanda | `docs/tarefas/2026-11-19-voltar-doca.md` |
| O que mudou e quando | `docs/tarefas/README.md` |

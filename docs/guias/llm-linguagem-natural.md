# Linguagem natural (LLM): como rodar

> **Outro robô:** os exemplos usam o `robot1`. Para outro, rode antes `infra/docker/lab.sh robo usar <nome>` e, nos comandos digitados, troque `/robot1` e o IP pelos dele (`docs/guias/acesso-ao-robo.md`, seção "Vários robôs").

Pacote `workspace/meu_ws/src/llm_tb4`: o nó recebe um pedido em português, interpreta com o Ollama (`qwen2.5:1.5b`) e, no robô com o freio solto, **move o robô**.

## Qual comando usar

| Quero | Comando que inicia o nó | O robô se move? |
|---|---|---|
| **Mandar o robô andar** (parte 1, passo 7) | `PARKING_BRAKE=false infra/docker/lab.sh robo llm` | **SIM**, a cada pedido, sem confirmação |
| Conferir no robô sem andar (parte 1, passo 6) | `infra/docker/lab.sh robo llm` | Não (freio ligado) |
| Treinar frases sem robô (parte 2) | `docker compose -f infra/compose/llm.yaml up -d` | **Nunca**: não alcança o robô |

Se o log mostra `[freio: não executado]`, o robô não vai andar: o freio está ligado ou é o ensaio sem robô.

> O código de movimento foi ensaiado só com um robô falso. Nos primeiros testes, uma pessoa ao lado, pronta para parar o robô. `docs/contexto/AGENTES.md` recomenda validar no simulador antes.

Todos os comandos rodam no PC do laboratório. Os blocos estão na ordem de execução.

## Qual robô

**Este guia vale para qualquer robô com perfil em `infra/lab/robos/`.** A escolha fica salva no PC e vale para todos os terminais, então **confira qual está salva antes de começar**:

```bash
infra/docker/lab.sh robo usar                     # mostra o robô em uso e os perfis
infra/docker/lab.sh robo parar                    # antes de trocar: derruba os serviços do robô anterior
infra/docker/lab.sh robo usar <nome>              # <nome> = robot1, robot3...: rotas do PC e teste da rede
```

A primeira linha de cada comando do `lab.sh robo` mostra o robô, o IP e o namespace: leia antes de digitar `SIM`.

A variável `ROBO` (em maiúsculas) só é necessária para valer sobre essa escolha em um terminal. Sem escolha nenhuma, vale o `robot1`. Nos comandos digitados com nome de tópico, troque `/robot1` pelo robô em uso.

## Antes do primeiro pedido: esperar e marcar a pose

Suba uma coisa de cada vez e **só avance quando o sinal da coluna da direita aparecer**:

| Ordem | O que fazer | Esperar |
|---|---|---|
| 1 | Subir a localização e o RViz (passo 3) | `Managed nodes are active` no log da localização; mapa na tela |
| 2 | **2D Pose Estimate** no RViz | O laser sobre as paredes |
| 3 | Subir o Nav2 (passos 4 e 5) | `Managed nodes are active` no log do Nav2 |
| 4 | Iniciar o nó (passo 6 ou 7) | `FREIO DESLIGADO` (ou o aviso do freio ligado) |
| 5 | **2D Pose Estimate de novo** | O laser sobre as paredes |
| 6 | **Só agora** abrir o `falar` e escrever o pedido | |

Essa ordem veio dos testes de 2026-11-25: os pedidos funcionaram respeitando as esperas e marcando a pose antes do `falar`.

# Parte 1: no robô

## 1. Preparar

Robô **na doca**, área livre.

```bash
cd ~/physical_ai                                        # raiz do projeto
docker compose -f infra/compose/llm.yaml down           # encerra o ensaio sem robô, se estiver no ar
infra/docker/lab.sh robo parar                          # derruba sobras do robô
systemctl is-active ollama                              # precisa responder "active"
ollama list                                             # precisa listar qwen2.5:1.5b
infra/docker/lab.sh robo checar-rede                    # precisa terminar em "REDE OK"
```

## 2. Conferir a bateria

```bash
# 0.20 ou mais para o robô sair da doca (0.78 = 78%)
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    ros2 topic echo --once /robot1/battery_state sensor_msgs/msg/BatteryState --qos-profile sensor_data --field percentage
```

Abaixo de `0.20`, deixe o robô carregando: o nó recusa sair.

## 3. Subir a localização e o RViz

```bash
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao   # AMCL + mapa
infra/docker/lab.sh robo subir rviz                                         # janela do RViz
```

No RViz: **2D Pose Estimate** na posição e direção reais do robô. O laser deve cair sobre as paredes.

Espere a localização antes de marcar a pose (pode levar cerca de 1 minuto):

```bash
docker logs tb4-robo-localizacao-1 2>&1 | grep "Managed nodes are active"
```

## 4. Subir o Nav2

```bash
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2          # navegação
```

## 5. Conferir o Nav2 (espere cerca de 1 minuto)

```bash
# Esperado: "Managed nodes are active", sem "CRITICAL" nem "Aborting" depois
docker logs tb4-robo-nav2-1 2>&1 | grep -E "Managed nodes are active|Aborting bringup|CRITICAL"
```

Se abortou, recrie só o Nav2: `infra/docker/lab.sh robo compose rm -sf nav2` e `infra/docker/lab.sh robo subir nav2`. A skill `/preflight-robo` confere os passos 1 a 5.

## 6. Nó com o freio ligado (não move)

```bash
infra/docker/lab.sh robo llm                      # TERMINAL 2: o nó
```

```bash
infra/docker/lab.sh robo falar                    # TERMINAL 3: escrever os pedidos
```

Escreva um pedido no terminal 3 e confira a linha `DECISAO` no terminal 2. Depois, **`Ctrl+C` no terminal 2**. O terminal 3 pode ficar aberto.

## 7. Nó com o freio solto (MOVE O ROBÔ)

**Antes:** pessoa ao lado, área livre, nenhuma patrulha rodando.

```bash
PARKING_BRAKE=false infra/docker/lab.sh robo llm   # TERMINAL 2: digite SIM
```

1. Espere aparecer `FREIO DESLIGADO` no terminal 2.
2. **Só então** refaça o **2D Pose Estimate** no RViz e confira o laser sobre as paredes: o nó precisa receber a localização depois de ligado.
3. **Depois da pose**, abra o terminal 3 (`infra/docker/lab.sh robo falar`) e faça o primeiro teste nesta ordem:

| Pedido | O que observar |
|---|---|
| `vá ao ponto 1` | Sai da doca e vai ao ponto 1 |
| `vá ao ponto 4` e, no caminho, só Enter | Para em cerca de um segundo. **Teste isto antes dos outros pedidos** |
| `vá ao ponto 4` e, no caminho, `vá ao ponto 1` | Cancela e muda de destino |
| `volte para a doca` | Aproxima e encaixa |

## Parar o robô

| Como | Efeito |
|---|---|
| Só Enter no terminal 3 | Envia "pare" |
| `Ctrl+C` no terminal 2, ou fechar esse terminal | Cancela a meta e encerra o nó |

**Fechar o terminal 3 não para o robô.** Se o PC cair ou o processo for morto à força, o Nav2 segue até o destino: a parada física é a garantia.

**Regras com o robô andando**

- **Qualquer mensagem cancela o trajeto**, mesmo que não seja um comando; se não for, o robô fica parado.
- Durante o dock e a saída da doca, a manobra termina e a última mensagem é obedecida. "pare" cancela na hora.
- Não há confirmação: uma interpretação errada move o robô até chegar outra mensagem.

## 8. Encerrar (sempre)

```bash
# terminal 2: Ctrl+C     terminal 3: Ctrl+D (se ficarem abertos, o "parar" os encerra)
infra/docker/lab.sh robo parar                    # encerra o nó, o falar e os serviços
docker ps                                         # não deve restar "tb4-robo-..."
```

## O robô não se mexe

| O que aparece | Causa e o que fazer |
|---|---|
| `[freio: não executado]` | Freio ligado ou ensaio sem robô: use o passo 7 |
| `bateria abaixo de 20%` | Carregar. Só "volte para a doca" é aceito |
| `localização nunca recebida` ou `sem map→odom recente` | Refazer o 2D Pose Estimate (o nó espera 20 s) |
| `sem estado recente da doca` ou `sem leitura recente da bateria` | `infra/docker/lab.sh robo checar-rede` |
| `servidor de ação indisponível` | Conferir o Nav2 (passo 5) |
| `há uma meta ativa de outro programa` | Encerrar o outro programa, ou "pare" |
| `o cancelamento não foi confirmado` | Conferir o robô; "pare" repete o cancelamento |
| `DECISAO ... recusar` | O pedido não foi entendido como comando; reescreva |
| `NINGUÉM RECEBEU` (terminal 3) | O nó não está no ar, ou ainda está iniciando |
| `Caractere inválido ignorado` (terminal 3) | Sobrou metade de uma letra acentuada; confira o texto mostrado, que é o enviado |

# Parte 2: ensaio sem robô (não move)

Serve para treinar frases. Usa bateria simulada e uma rede ROS própria: **o robô nunca recebe nada**.

```bash
cd ~/physical_ai
docker compose -f infra/compose/llm.yaml up -d          # compila e inicia
docker compose -f infra/compose/llm.yaml logs -f llm    # deixar neste terminal; Ctrl+C só fecha o log
```

Em outro terminal, troque o texto depois de `data:`:

```bash
docker compose -f infra/compose/llm.yaml exec llm bash -c \
  'source /opt/ros/humble/setup.bash; ros2 topic pub --once -w 1 /robot1/user_input std_msgs/msg/String "data: vai pra janela"'
```

| Experimente | Esperado no log |
|---|---|
| `vai pra janela` | `ir_para:ponto_4` |
| `vai pra geladeira` | `ir_para:ponto_2` |
| `vá para x -3.5 y -3.0` | `ir_para_coordenadas:-3.5,-3` |
| `vá para x 100 y 100` | `recusar` (fora do mapa) |
| `undock` | `sair_da_base` |llm
| `volte para a doca` | `voltar_para_base` |
| `pare` | `parar` |

```bash
docker compose -f infra/compose/llm.yaml down           # encerrar
```

Uma frase por vez, sem nó, e medição do modelo:

```bash
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.interpretador "vai pra mesa central")   # mostra a decisão
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar)    # acertos e tempo nas frases de teste
```

Os locais e seus nomes estão em `workspace/meu_ws/src/llm_tb4/config/destinos.json`.

# Depois de mudar código, prompt ou destinos

O nó do robô recompila a cada `lab.sh robo llm`; o do ensaio, a cada `down` e `up -d`.

```bash
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo/workspace/meu_ws/src/llm_tb4 \
  physical-ai:base python3 -m pytest -q -p no:cacheprovider                                       # testes sem modelo
docker run --rm --network none -e COMPILAR_WS=patrulha_tb4,llm_tb4 -e ROS_DOMAIN_ID=43 -e ROS_LOCALHOST_ONLY=1 \
  -v "$PWD/workspace:/workspace:ro" -v "$PWD/workspace/mapas:/mapas:ro" physical-ai:base \
  python3 /workspace/meu_ws/src/llm_tb4/test/ensaio_no.py                                         # ensaio do nó (freio ligado)
docker run --rm --network none -e COMPILAR_WS=patrulha_tb4,llm_tb4 -e ROS_DOMAIN_ID=43 -e ROS_LOCALHOST_ONLY=1 \
  -v "$PWD/workspace:/workspace:ro" -v "$PWD/workspace/mapas:/mapas:ro" physical-ai:base \
  python3 /workspace/meu_ws/src/llm_tb4/test/ensaio_execucao.py                                   # execução, com robô falso
```

Explicação do pacote: `workspace/meu_ws/src/llm_tb4/README.md`. Plano, decisões e medições: `specs/llm-integracao/PLANO.md`.

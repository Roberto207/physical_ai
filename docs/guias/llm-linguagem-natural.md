# Linguagem natural (LLM): como rodar

Pacote `workspace/meu_ws/src/llm_tb4`: o nó recebe um pedido em português, interpreta com o Ollama (`qwen2.5:1.5b`) e, se o freio estiver solto, **move o robô**.

| Modo | Como se inicia | Move o robô? |
|---|---|---|
| Ensaio isolado (partes A) | `infra/compose/llm.yaml` | **Não.** Não alcança o robô |
| Robô, freio ligado (parte B) | `lab.sh robo llm` | **Não.** Só interpreta, usando a bateria real |
| Robô, freio solto (parte C) | `PARKING_BRAKE=false lab.sh robo llm` | **SIM**, a cada pedido, sem confirmação |

> **O código de execução ainda não rodou no simulador nem no robô.** Foi ensaiado só com um robô falso. `docs/contexto/AGENTES.md` manda validar no simulador antes do robô.

Todos os comandos rodam no PC do laboratório. Os blocos estão na ordem de execução.

# A. Ensaio isolado

## 1. Conferir o modelo

```bash
cd ~/physical_ai                                  # raiz do projeto
systemctl is-active ollama                        # precisa responder "active"
ollama list                                       # precisa listar qwen2.5:1.5b
ollama pull qwen2.5:1.5b                          # só se não estiver na lista (cerca de 986 MB)
```

## 2. Iniciar o nó

```bash
docker compose -f infra/compose/llm.yaml up -d          # compila o pacote e inicia
docker compose -f infra/compose/llm.yaml logs -f llm    # deixar neste terminal; Ctrl+C só fecha o log
```

Pronto quando aparecer `FREIO DE ESTACIONAMENTO: nada será executado.` e, alguns segundos depois, o nó aceitar pedidos. Um erro `o modelo ... não respondeu` indica o Ollama parado.

## 3. Enviar pedidos (em outro terminal)

```bash
cd ~/physical_ai
docker compose -f infra/compose/llm.yaml exec llm bash -c \
  'source /opt/ros/humble/setup.bash; ros2 topic pub --once -w 1 /robot1/user_input std_msgs/msg/String "data: vai pra janela"'
```

Troque o texto depois de `data:`. A resposta aparece no terminal do log, em uma linha `DECISAO: ...`.

| Experimente | Esperado no log |
|---|---|
| `vai pra janela` | `ir_para:ponto_4` |
| `vai pra geladeira` | `ir_para:ponto_2` |
| `vá para x -3.5 y -3.0` | `ir_para_coordenadas:-3.5,-3` |
| `vá para x 100 y 100` | `recusar` (fora do mapa) |
| `undock` | `sair_da_base` |
| `volte para a doca` | `voltar_para_base` |
| `pare` | `parar` |

Os locais e seus nomes estão em `workspace/meu_ws/src/llm_tb4/config/destinos.json`.

## 4. Testar sem o nó, uma frase por vez

```bash
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.interpretador "vai pra mesa central")   # mostra a decisão
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar)    # mede acertos e tempo em todas as frases de teste
```

## 5. Encerrar (sempre)

```bash
docker compose -f infra/compose/llm.yaml down           # para e remove o contêiner do nó
docker ps                                               # não deve restar "tb4-llm-..."
```

# B. No robô, com o freio ligado (não move)

```bash
cd ~/physical_ai
infra/docker/lab.sh robo parar                    # derruba sobras
infra/docker/lab.sh robo checar-rede              # precisa terminar em "REDE OK"
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao
infra/docker/lab.sh robo subir rviz               # no RViz: 2D Pose Estimate na pose real
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2
```

A skill `/preflight-robo` confere esses passos e o estado dos nós.

```bash
infra/docker/lab.sh robo llm                      # terminal 2: o nó (freio ligado)
infra/docker/lab.sh robo falar                    # terminal 3: escrever os pedidos
```

Confira no terminal 2 que as frases viram a `DECISAO` esperada. Encerre o nó com `Ctrl+C` antes de seguir.

# C. No robô, movendo

**Antes:** pessoa ao lado capaz de parar o robô, área livre, nenhuma patrulha rodando, serviços da parte B no ar.

**Terminal 2: o nó**

```bash
PARKING_BRAKE=false infra/docker/lab.sh robo llm  # MOVE O ROBÔ: pede SIM
```

Espere `FREIO DESLIGADO` e, em seguida, o nó ficar pronto. **Só então** refaça o **2D Pose Estimate** no RViz: o nó precisa receber a localização depois de ligado.

**Terminal 3: os pedidos**

```bash
infra/docker/lab.sh robo falar                    # Enter vazio envia "pare"
```

| Primeiro teste, nesta ordem | O que observar |
|---|---|
| `vá ao ponto 1` | Sai da doca e vai ao ponto 1 |
| `vá ao ponto 4` e, no caminho, Enter vazio | Para em cerca de um segundo. **Teste isto antes de confiar nos outros pedidos** |
| `vá ao ponto 4` e, no caminho, `vá ao ponto 1` | Cancela e muda de destino |
| `volte para a doca` | Aproxima e encaixa |

**Regras do nó com o robô andando**

- **Qualquer mensagem cancela o trajeto**, mesmo que não seja um comando; se não for, o robô fica parado.
- Durante o dock e a saída da doca, a manobra termina e a última mensagem é obedecida. "pare" cancela na hora.
- Não há confirmação: uma interpretação errada move o robô até chegar outra mensagem.

**Para parar:** Enter vazio no `falar`; `Ctrl+C` no terminal do nó; fechar esse terminal. Os três cancelam a meta. **Fechar o `falar` não para o robô.** Se o processo morrer à força (queda do PC, falta de memória), o Nav2 segue até o destino: a parada física continua sendo a garantia.

| Mensagem no log | O que fazer |
|---|---|
| `aguardando ... sem map→odom recente` ou `localização nunca recebida` | Refazer o 2D Pose Estimate (o nó espera 20 s) |
| `há uma meta ativa de outro programa` | Encerrar o outro programa, ou "pare" |
| `bateria abaixo de 20%` | Só "volte para a doca" é aceito |
| `o cancelamento não foi confirmado` | Conferir o robô; "pare" repete o cancelamento |

**Encerrar (sempre)**

```bash
# terminal 2: Ctrl+C     terminal 3: Ctrl+D
infra/docker/lab.sh robo parar                    # encerra o nó (se sobrou) e depois o resto
docker ps                                         # não deve restar "tb4-robo-..."
```

## Depois de mudar código, prompt ou destinos

```bash
docker compose -f infra/compose/llm.yaml down && docker compose -f infra/compose/llm.yaml up -d   # recompila
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

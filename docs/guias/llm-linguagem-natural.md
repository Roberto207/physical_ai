# Linguagem natural (LLM): como rodar

Pacote `workspace/meu_ws/src/llm_tb4`: o nó recebe um pedido em português, interpreta com o Ollama (`qwen2.5:1.5b`) e registra a ação no log.

> **O nó não move o robô.** Não há código de execução, e o Compose abaixo é **isolado do robô**: pode rodar com ele ligado ou desligado.

Todos os comandos rodam no PC do laboratório. Os blocos estão na ordem de execução.

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

## Depois de mudar código, prompt ou destinos

```bash
docker compose -f infra/compose/llm.yaml down && docker compose -f infra/compose/llm.yaml up -d   # recompila
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo/workspace/meu_ws/src/llm_tb4 \
  physical-ai:base python3 -m pytest -q -p no:cacheprovider                                       # testes sem modelo
docker run --rm --network none -e COMPILAR_WS=patrulha_tb4,llm_tb4 -e ROS_DOMAIN_ID=43 -e ROS_LOCALHOST_ONLY=1 \
  -v "$PWD/workspace:/workspace:ro" -v "$PWD/workspace/mapas:/mapas:ro" physical-ai:base \
  python3 /workspace/meu_ws/src/llm_tb4/test/ensaio_no.py                                         # ensaio do nó
```

Explicação do pacote: `workspace/meu_ws/src/llm_tb4/README.md`. Plano, decisões e medições: `specs/llm-integracao/PLANO.md`.

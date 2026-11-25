# llm_tb4: linguagem natural para o TurtleBot 4

Missão 2 do projeto (`docs/contexto/projeto.md`). Pacote ROS 2 baseado no `turtlebot4_openai_tutorials` oficial, com um modelo local. Plano, desvios e medições: `specs/llm-integracao/PLANO.md`.

**Estado:** o nó interpreta e executa com o `TurtleBot4Navigator`. O freio (`parking_brake`) vem ligado. A execução foi ensaiada só com um robô falso: **falta simulador e robô**.

## Modelo

**Ollama** com `qwen2.5:1.5b` ([página do modelo](https://ollama.com/library/qwen2.5)), instalado no PC do laboratório como serviço em `127.0.0.1:11434`.

```bash
ollama list                      # o modelo está baixado?
ollama pull qwen2.5:1.5b         # baixar (cerca de 986 MB)
systemctl status ollama          # o serviço está ativo?
```

## Rodar o nó (isolado do robô)

Passo a passo em `docs/guias/llm-linguagem-natural.md`. Resumo, na raiz do repositório:

```bash
docker compose -f infra/compose/llm.yaml up -d            # compila e inicia
docker compose -f infra/compose/llm.yaml logs -f llm      # decisões (Ctrl+C só fecha o log)

# enviar um pedido
docker compose -f infra/compose/llm.yaml exec llm bash -c \
  'source /opt/ros/humble/setup.bash; ros2 topic pub --once -w 1 /robot1/user_input std_msgs/msg/String "data: vai pra janela"'

# aceita novo pedido? (só publica quando muda)
docker compose -f infra/compose/llm.yaml exec llm bash -c \
  'source /opt/ros/humble/setup.bash; ros2 topic echo /robot1/ready_for_input'

docker compose -f infra/compose/llm.yaml down             # encerrar
```

Depois de mudar o código, `down` e `up -d` de novo.

## Tópicos e parâmetros

| Nome | Tipo | Uso |
|---|---|---|
| `user_input` | `std_msgs/String`, entrada | O pedido |
| `ready_for_input` | `std_msgs/Bool`, saída | Verdadeiro quando uma mensagem nova será atendida. Falso só enquanto, parado, interpreta um pedido |
| `dock_status`, `tf`, estados das ações | entrada, com o freio solto | Condições antes de mover |
| `battery_state` | `sensor_msgs/BatteryState`, entrada | Carga usada na validação |
| `model_name` | parâmetro | Modelo do Ollama |
| `parking_brake` | parâmetro | `true` (padrão): nada é enviado. `false`: **move o robô** |
| `ollama_url`, `mapa`, `arquivo_pontos` | parâmetros | Endereço do Ollama, mapa e arquivo de onde ler os pontos |
| `bateria_simulada` | parâmetro | Carga para ensaio (-1 usa a real); recusada com o freio solto |

## O que pode ser pedido

| Pedido | Exemplo | Ação |
|---|---|---|
| Um local cadastrado | "vai pra janela" | `ir_para` |
| Uma coordenada do mapa | "vá para x -3.5 y -3.0 virado para o leste" | `ir_para_coordenadas` |
| Voltar à doca | "volte para a doca" | `voltar_para_base` |
| Encaixar | "dock" | `encaixar` |
| Sair da doca | "undock", "saia da doca" | `sair_da_base` |
| Parar | "pare" | `parar` |

- Coordenadas: os números são lidos por código, não pelo modelo. Formatos: `x -1.5 y 0`, `-3.5, -3.0`, `coordenada -1 -2`, `(-0,5; -0,8)`. São recusadas fora do mapa, em área não mapeada, ocupada ou a menos de 0,25 m de obstáculo.
- A direção usa a convenção do `TurtleBot4Directions`: norte 0°, oeste 90°, sul 180°, leste 270°.
- Ir e sair da doca exigem bateria a partir de 20%.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `llm_tb4/no_linguagem_natural.py` | O nó: entrada, Ollama, sinais de encerramento |
| `llm_tb4/missao.py` | Quando mover, cancelar ou ignorar. Sem ROS |
| `llm_tb4/execucao.py` | Clientes de ação, sensores e cancelamento |
| `llm_tb4/pontos.py` | Pontos da patrulha, direção de chegada e proteção da doca |
| `llm_tb4/falar.py` | Terminal para enviar pedidos (`ros2 run llm_tb4 falar`) |
| `llm_tb4/interpretador.py` | Frase → ação validada: pedido de parar e `dock`/`undock` decididos por código; negação e dois destinos recusados; o resto vai ao modelo |
| `llm_tb4/validar_acao.py` | Aceita só as ações da tabela |
| `llm_tb4/coordenadas.py`, `llm_tb4/mapa.py` | Lê coordenadas e confere no mapa |
| `llm_tb4/avaliar.py` | Mede o modelo real. Sai com 2 se o modelo não responder e com 1 se alguma consulta falhar |
| `config/destinos.json` | Locais que podem ser pedidos |
| `prompts/comandos.txt` | Instruções e exemplos enviados ao modelo |
| `launch/natural_language_nav_launch.py` | Inicia o nó |
| `test/` | Testes, frases de medição e o ensaio do nó |

## Testar

Na raiz do repositório:

```bash
# mostrar a decisão para uma frase, sem ROS (usa o Ollama)
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.interpretador "vai pra geladeira")
# medir o modelo real com as frases de test/frases/
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar)
# testes sem modelo (o python3 do PC não tem pytest)
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo/workspace/meu_ws/src/llm_tb4 \
  physical-ai:base python3 -m pytest -q -p no:cacheprovider
# ensaios sem rede, com Ollama e robô falsos: comandos no topo de test/ensaio_no.py e test/ensaio_execucao.py
```

## Limites

- O modelo erra: perguntas e afirmações podem virar ação. Pedidos de parar em formas novas podem não ser reconhecidos.
- Sem confirmação por ação: com o freio solto, uma interpretação errada move o robô.
- Se o processo morrer à força, o Nav2 segue até o destino.
- No robô real use `lab.sh robo llm`, não o `ros2 launch`: o launch morre num `docker stop` antes de o nó cancelar a meta.

# Comandos por LLM

O nó `llm/no_llm.py` recebe um pedido em português no tópico `<ns>/user_input`. Ele interpreta o pedido com o Ollama (`qwen2.5:1.5b`, local) e, com o freio desligado, **move o robô**. A decisão de desenho está no ADR-005: o modelo escolhe uma ação em JSON e nada do que ele escreve é executado.

## Como o pedido vira movimento

| Etapa | Onde | O que faz |
|---|---|---|
| 1. Regras | `llm/interpretar.py` | "pare" e variações viram `parar` sem consultar o modelo. Negação ("não vá..."), sequência ("depois", "pontos") e frase com mais de 200 caracteres são recusadas. "dock" e "undock" sozinhos são decididos pelo código, porque o 1.5B trocava um pelo outro |
| 2. Modelo | `perguntar_ao_ollama` | `llm/prompt.txt` com os locais, mais o pedido. Resposta `{acao, local}` restrita por JSON Schema (`format`), com `temperature 0` e `seed 0` |
| 3. Conferência | `decidir` | A ação existe e o local está em `LOCAIS` (`ponto_1` a `ponto_4`). Sair da doca exige bateria válida e de pelo menos 20% |
| 4. Execução | `llm/no_llm.py` + `robo.py` | Sai da doca se estiver encaixado e vai ao ponto, olhando para o ponto seguinte, ou volta ao ponto 1 e encaixa |

**Ações:**

| Ação | O que o robô faz |
|---|---|
| `ir_para` | Vai ao local pedido |
| `voltar_para_base` | Volta ao ponto 1 e encaixa |
| `encaixar` | Só o dock |
| `sair_da_base` | Só o undock |
| `parar` | Cancela a meta |
| `nenhuma` | Recusa o pedido |

**Locais e o que o modelo lê de cada um:**

| Local | Descrição |
|---|---|
| `ponto_1` | Doca e impressora |
| `ponto_2` | Geladeira e micro-ondas |
| `ponto_3` | Porta |
| `ponto_4` | Janela e mesa central |

As coordenadas ficam em `robo.py` (`PONTOS`), as mesmas da patrulha.

## Rodar no robô

**Antes:**

- passos 1 a 3 de `docs/guias/como-rodar.md` (rede, localização com 2D Pose Estimate e Nav2);
- bateria de 20% ou mais;
- nenhuma patrulha rodando.

```bash
scripts/llm.sh                 # TERMINAL 1: freio ligado, interpreta e registra, não move
scripts/falar.sh               # TERMINAL 2: cada linha é um pedido; só Enter = "pare"
```

No terminal 1 aparece `ACEITO: '<pedido>' -> ir_para:ponto_2 (modelo) [freio: não executado]` ou `RECUSADO: ...`. Para mover:

```bash
scripts/llm.sh mover           # TERMINAL 1: O ROBÔ SE MOVE a cada pedido aceito
```

1. Espere `FREIO DESLIGADO` no terminal 1. Antes disso, o nó confere `map→odom` e as ações do Nav2.
2. Refaça o **2D Pose Estimate** e confira o laser. Em 25/11, os pedidos só funcionaram com a pose marcada depois de o nó subir.
3. No terminal 2, faça o primeiro teste nesta ordem:

| Pedido | O que observar |
|---|---|
| `vá ao ponto 1` | Sai da doca e vai ao ponto 1 |
| `vá ao ponto 4` e, no caminho, só Enter | Para em cerca de um segundo. **Teste isto antes dos outros** |
| `vá ao ponto 4` e, no caminho, `vá ao ponto 1` | Cancela e muda de destino |
| `volte para a doca` | Vai ao ponto 1 e encaixa |

**Regras com o robô andando:**

- **Qualquer mensagem cancela o trajeto.** Depois ela é interpretada; se não for um comando, o robô fica parado.
- Durante o dock e o undock, só "pare" cancela. Outra mensagem espera a manobra terminar.
- Não há confirmação: uma interpretação errada move o robô até chegar outra mensagem.
- `Ctrl+C` no terminal 1 e `scripts/parar.sh` cancelam a meta antes de sair.
- **Fechar o terminal 2 não para o robô.** Se o PC cair, o Nav2 segue até o destino: a garantia é a pessoa ao lado.

## Quando não se mexe

| Mensagem | O que fazer |
|---|---|
| `[freio: não executado]` | Use `scripts/llm.sh mover` |
| `bateria insuficiente ou desconhecida para sair` | Carregar. "volte para a doca" continua aceito |
| `Sem map→odom recente` (na subida) | Refazer o 2D Pose Estimate e subir o nó de novo |
| `estado da doca desconhecido` | O `dock_status` não chega: `scripts/checar.sh` |
| `Servidores de ação indisponíveis` | Conferir o Nav2 (`docker logs tb_nav2`) |
| `RECUSADO: ... o modelo não reconheceu um comando` | Reescreva o pedido com um dos locais |
| `falha ao consultar o modelo` | O Ollama não respondeu: `systemctl status ollama` |
| `NINGUÉM RECEBEU` (terminal 2) | O nó não está no ar, ou ainda está subindo |

## Sem robô

Uma frase, só a interpretação (precisa do Ollama no PC):

```bash
python3 llm/interpretar.py "vai pra mesa central"
```

Para medir o prompt depois de mudar `llm/prompt.txt`, os locais ou o modelo, rode as 388 frases de `llm/frases.json`, que vêm dos ensaios de 25/11:

```bash
python3 llm/avaliar.py              # todos os grupos
python3 llm/avaliar.py estresse     # um grupo
```

O número que importa é "moveria errado": o pedido virou um movimento que não era o pedido. Também rode `python3 -m pytest tests` (sem Ollama).

## Limites conhecidos

- Perguntas, condições e afirmações ainda podem virar ação (51 das 265 frases dos avaliadores em 25/11, antes da reformulação). Medir de novo com `llm/avaliar.py`.
- Sem coordenadas livres desde 26/11 ("vá para x 1 y 2" é recusado).
- Um pedido por vez. Não há sequência de destinos.

# O prompt da LLM neste projeto

| Item | Onde |
|---|---|
| Modelo | Ollama local, `qwen2.5:1.5b`, em `127.0.0.1:11434` |
| Prompt | `workspace/meu_ws/src/llm_tb4/prompts/comandos.txt` |
| Destinos que entram no prompt | `workspace/meu_ws/src/llm_tb4/config/destinos.json` |
| Chamada (esquema, temperatura 0, tempo limite) | `workspace/meu_ws/src/llm_tb4/llm_tb4/interpretador.py` |
| Validador | `workspace/meu_ws/src/llm_tb4/llm_tb4/validar_acao.py` |
| Casos de teste com o modelo real | `workspace/meu_ws/src/llm_tb4/test/frases/*.json` |
| Plano e medições | `specs/llm-integracao/PLANO.md` |

## Medir antes e depois de mudar o prompt

```bash
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar)                          # todos os conjuntos, com o modelo real
(cd workspace/meu_ws/src/llm_tb4 && python3 -m llm_tb4.avaliar test/frases/reserva.json) # um conjunto
docker run --rm --network none -v "$PWD:/repo:ro" -w /repo/workspace/meu_ws/src/llm_tb4 physical-ai:base python3 -m pytest -q -p no:cacheprovider
```

- Compare o número de frases que moveriam o robô errado e os pedidos de parar não reconhecidos,
  não só os acertos.
- Um conjunto usado para ajustar o prompt deixa de medir generalização: escreva um conjunto novo
  **antes** de ajustar e rode-o uma vez.
- O subagente `prompt-critico` simula respostas; ele complementa a medição e não a substitui.
- Parar, negação, bateria, coordenadas e `dock`/`undock` são decididos em código; não os transfira para o prompt.

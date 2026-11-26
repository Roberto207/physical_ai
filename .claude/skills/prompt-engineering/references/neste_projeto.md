# O prompt da LLM neste projeto

| Item | Onde |
|---|---|
| Modelo | Ollama local, `qwen2.5:1.5b`, em `127.0.0.1:11434` |
| Prompt | `llm/prompt.txt` |
| Locais que entram no prompt | `LOCAIS` em `llm/interpretar.py` |
| Chamada (esquema, temperatura 0, tempo limite) e regras em código | `llm/interpretar.py` |
| Casos de teste com o modelo real | `llm/frases.json` (388 frases em 8 grupos) |
| Decisão de desenho | `docs/decisoes/ADR-005-llm-escolhe-acao-em-json.md` |

## Medir antes e depois de mudar o prompt

```bash
python3 llm/avaliar.py              # todos os grupos, com o modelo real
python3 llm/avaliar.py reserva      # um grupo
python3 -m pytest tests             # parte pura, sem modelo
```

- Compare o número de frases que moveriam o robô errado e os pedidos de parar não reconhecidos,
  não só os acertos.
- Um conjunto usado para ajustar o prompt deixa de medir generalização: escreva um conjunto novo
  **antes** de ajustar e rode-o uma vez.
- O subagente `prompt-critico` simula respostas; ele complementa a medição e não a substitui.
- Parar, negação, sequência, bateria e `dock`/`undock` são decididos em código; não os transfira para o prompt.

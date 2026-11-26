# ADR-005: O LLM escolhe uma ação em JSON, não escreve código

**Status:** Aceito em 2026-11-26 (registra a decisão de 2026-11-25 do `specs/llm-integracao/PLANO.md`, que saiu)
**Data:** 2026-11-26

## Contexto

O tutorial oficial (`natural_language_nav`) pede código Python ao modelo e o executa com `exec()`. Com um modelo local pequeno (`qwen2.5:1.5b`), isso dá ao modelo acesso a qualquer chamada do robô.

## Decisão

O Ollama responde `{acao, local}` restrito por JSON Schema. O código confere a ação, o local e a bateria antes de mover. "Pare", negação, sequência e dock/undock sozinhos são decididos por regra, sem o modelo. O freio (ligado por padrão) interpreta sem mover.

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| `exec()` com validador de AST (repo do colega) | Mais superfície; o JSON já limita o que existe |
| Coordenadas livres no texto | Retirado na reformulação (decisão do Roberto) |

## Consequências

### Positivas

- Nada que o modelo escreve é executado.

### Negativas

- Cada ação nova pede código e um exemplo no `prompt.txt`.

### Mitigação

- `llm/avaliar.py` mede o prompt com as 388 frases de `llm/frases.json`.

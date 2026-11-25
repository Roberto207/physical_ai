# Integração com LLM

Missão 2 do projeto (`docs/contexto/projeto.md`): comandar o TurtleBot 4 por linguagem natural.

## O que existe

| Arquivo | O que faz |
|---|---|
| `validar_acao.py` | Recebe a ação proposta (um dicionário) e responde se pode ser executada. Ações: `ir_para` (um local conhecido, bateria a partir de 20%), `voltar_para_base` e `parar` |
| `test_validar_acao.py` | Casos aceitos e recusados |

```bash
(cd workspace/llm && python3 -m pytest -q)        # precisa de pytest
```

**Ainda não existe:** chamada a uma LLM, nó ROS, execução da ação no robô e a tabela de locais do `mapa_lab_novo`.

## Regra de desenho

A LLM só escolhe entre ações discretas validadas; nada do que ela escreve é executado como código (sem `exec`). O registro está em `docs/decisoes/README.md` como proposta a confirmar com a equipe. O tutorial oficial `turtlebot4_openai_tutorials` serve de referência, não de base.

## De onde reaproveitar

- Locais: `workspace/mapas/pontos_mapa_lab_novo.md`.
- Navegar, esperar a localização, encaixar na doca: funções de `workspace/patrulha_oficial/patrol_loop.py`.

Decisões em aberto: `docs/contexto/pendencias.md`.

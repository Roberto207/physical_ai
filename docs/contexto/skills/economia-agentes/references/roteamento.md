# Roteamento: tarefa → agente → modelo → esforço

Quando a coluna "Use" for diferente do que o agente herdaria, passe `model`/`effort` na chamada. `Explore`, `general-purpose` e `Plan` vêm com o Claude Code; o `sdd-ears-critico` e o `prompt-critico` são instalados junto com as skills `sdd` e `prompt-engineering`.

| Tarefa | Agente | Use | Esforço |
|---|---|---|---|
| Pontual ou edição pequena | direto | Sonnet (sugira /model) | low |
| Feature com escopo claro (nó da patrulha, validador da LLM) | direto | Sonnet | medium |
| Bug difícil ou arquitetura (Nav2, TF, descoberta DDS) | direto ou Plan | Opus | high |
| Varredura no repositório | Explore | haiku | low |
| Rodar `pytest`, `colcon test`, `docker build` e resumir a saída | general-purpose | haiku | low |
| Ler logs longos da patrulha ou do Nav2 e apontar a primeira falha | general-purpose | sonnet | medium |
| Pesquisa em documentação oficial (TurtleBot 4, Nav2, Create 3) | general-purpose, 2 a 4 | sonnet | medium |
| Criticar os critérios EARS de um `DEFINE.md` | sdd-ears-critico | sonnet | medium |
| Atacar um prompt candidato com casos de teste | prompt-critico | opus | medium |
| Qualquer ação no robô físico | direto, com autorização | sessão | medium |
| Problema muito difícil | direto | Opus | high |

Fable: só com créditos confirmados (Passo 1).

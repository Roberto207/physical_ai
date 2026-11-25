# Temperatura e checklist de hardening para produção

## Tabela de temperatura

| Faixa | Uso | Por quê |
|---|---|---|
| 0.0–0.3 | Factual, extração, classificação, RAG com citação, qualquer coisa determinística | Minimiza variância — a mesma entrada deve gerar (quase) a mesma saída |
| 0.4–0.7 | Resumo, reescrita, tarefas com alguma variação estilística aceitável | Equilíbrio entre consistência e naturalidade |
| 0.8–1.0+ | Brainstorm, geração de variações, texto criativo/persuasivo | Variância é o ponto — você quer diversidade de saída |

Em produção, trave a temperatura num objeto de config imutável (ex.: um `dataclass` com
`frozen=True`), e não num número solto na chamada. Isso evita que uma temperatura alta de
um teste exploratório vá junto quando a chamada for copiada.

## Checklist de hardening (Fase 5 da skill)

- [ ] **Temperatura via gate central**, não hardcoded na chamada individual.
- [ ] **Schema de saída explícito** (JSON com campos nomeados, ou formato estrito de uma
      palavra) sempre que algo downstream vai fazer parsing — nunca confie em regex sobre
      prosa livre para extrair algo que o modelo pode formatar de saída.
- [ ] **Fail-open vs. fail-closed decidido conscientemente** para qualquer
      guardrail/classificador — não é um acidente de implementação, é uma escolha de
      design que depende de qual erro é mais caro no seu domínio.
- [ ] **Pelo menos um exemplo negativo** cobrindo a categoria/caso mais ambíguo.
- [ ] **Regras numeradas rastreáveis** — se o prompt tem uma lista de regras, cada uma
      deveria ter um motivo identificável (mesmo que não escrito no prompt em si, ao
      menos documentado em algum lugar).

## O que vai no system prompt

O system prompt vale para a conversa inteira. Coloque nele: papel, restrições permanentes e
formato de saída padrão. Não coloque instruções de uma única tarefa (vão no prompt de
usuário): misturar os dois torna o system prompt difícil de reutilizar e expõe mais
contexto a prompt injection.

## Meta-prompting

Técnica de usar o próprio LLM para gerar, criticar ou refinar um prompt — por exemplo,
pedir "aqui está meu prompt e 3 casos onde ele falhou, sugira uma versão revisada". É
exatamente o papel que o subagente `prompt-critico` desta skill cumpre de forma
estruturada e guardada (crítica sem propor a correção, para não virar coautor
silencioso da própria avaliação) — meta-prompting solto na conversa principal tende a
ser mais superficial porque o mesmo contexto que gerou o prompt original influencia a
"crítica".

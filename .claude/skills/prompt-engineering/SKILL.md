---
name: prompt-engineering
description: >
  Use sempre que o usuário pedir para escrever, revisar, depurar ou melhorar QUALQUER
  prompt — de sistema, de usuário, few-shot, de classificação, de agente — por exemplo
  "ajuda a escrever esse prompt", "esse prompt não está funcionando direito", "melhora
  esse system prompt", "preciso de um prompt pra classificar X", "por que o modelo está
  ignorando essa regra", "qual técnica de prompting uso aqui", "qual temperatura eu uso",
  "revisa esse prompt antes de eu subir pra produção", ou qualquer pedido de engenharia de
  prompt / prompt design / few-shot / chain-of-thought. Funciona tanto para desenhar um
  prompt novo quanto para diagnosticar um que já existe e está falhando. SEMPRE constrói
  um conjunto mínimo de casos de teste (incluindo casos adversariais) antes de considerar
  qualquer versão do prompt como final, e PARA para aprovação explícita antes de gravar o
  prompt definitivo em código de produção — nunca entrega um prompt sem testá-lo contra
  pelo menos um caso que tenta quebrá-lo.
argument-hint: '"<tarefa ou prompt existente>" [--novo|--diagnosticar] [--producao|--exploratorio]'
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "AskUserQuestion", "Agent"]
---

# Engenharia de Prompt — processo empírico, não palpite

Esta skill trata prompt engineering como **ciência empírica**, não como tentativa e erro
às cegas: definir critério de sucesso → construir casos de teste (incluindo
adversariais) → escrever um rascunho → criticar/iterar → endurecer para produção →
entregar. **Nunca considere um prompt "pronto" sem ter definido o que "bom" significa e
sem ter testado contra pelo menos um caso desenhado para quebrá-lo.**

Regra de ouro por trás de tudo: escreva as instruções que você daria a uma pessoa
competente mas sem contexto prévio do seu domínio — clareza simples bate complexidade
impressionante quase sempre.

## Quando NÃO usar

Pedido de resposta única e pontual para uma pergunta (não é um prompt reutilizável).
Ajuste cosmético de uma frase num prompt já testado, sem mudança de comportamento
esperado — só edite direto.

## Fase 0 — Modo e tarefa

1. `AskUserQuestion` ou inferência clara do texto do usuário:
   - **Novo** vs. **diagnosticar** um prompt existente (se diagnosticar: peça o texto do
     prompt atual + pelo menos um exemplo real de saída que falhou).
   - **Neste projeto**, leia `docs/contexto/AGENTES.md` antes. Prompt cuja saída move o
     robô é sempre **produção**, é testado sem o robô, e a saída passa por um validador.
     Leia também `references/neste_projeto.md` (modelo, arquivos e como medir).
   - **Exploratório** (rascunho pra testar uma ideia na conversa) vs. **produção** (vai
     virar código) — isso afeta o rigor da Fase 5.
2. **Defina o critério de sucesso explicitamente antes de continuar.** "O que 'bom'
   significa aqui" tem que virar uma frase objetiva (ex.: "classifica corretamente em
   >95% dos casos de teste, nunca inventa uma fonte que não está no contexto"). Sem isso
   a iteração da Fase 4 nunca converge — é o erro mais comum desta skill.
3. Escolha a faixa de temperatura-alvo:

   | Faixa | Uso |
   |---|---|
   | 0.0–0.3 | Factual, determinístico, extração, classificação, RAG com citação |
   | 0.4–0.7 | Balanceado — resumo, reescrita, tarefas com alguma variação aceitável |
   | 0.8–1.0+ | Criativo — brainstorm, geração de variações, texto persuasivo |

## Fase 1 — Casos de teste (mini-eval)

Antes de escrever qualquer versão do prompt, monte 5–10 casos de teste: entradas
representativas do caso feliz, casos-limite, e **pelo menos um caso adversarial
explícito** (uma entrada desenhada para tentar fazer o prompt ignorar uma regra, vazar
instrução do sistema, ou sair do formato esperado). Escreva isso como uma lista simples
`entrada → comportamento esperado`.

## Fase 2 — Anatomia e técnica

Leia `references/anatomia_e_vocabulario.md` e escolha a anatomia (Role, Context, Task,
Format, Examples, Constraints/Tone — nem toda parte é sempre necessária). Leia
`references/tecnicas_ladder.md` e, se a tarefa exigir raciocínio não-trivial,
`references/tecnicas_avancadas.md`; escolha a técnica pela tabela de decisão
custo×complexidade de cada arquivo — não use Chain-of-Thought ou Tree-of-Thought por
padrão em tarefas simples, o custo extra de tokens tem que se justificar.

## Fase 3 — Rascunho

Escreva o prompt aplicando a anatomia e técnica escolhidas. Leia
`references/padroes_de_producao.md` e aplique os padrões que fizerem sentido para
o caso: regras numeradas (facilita apontar qual regra falhou depois), schema de saída
forçado quando algo downstream vai fazer parsing, defesa em camadas (um filtro barato
antes de um LLM caro/lento quando o volume justificar), e few-shot com **exemplo
positivo e negativo** sempre que houver ambiguidade de categoria.

## Fase 4 — Crítica adversarial e iteração

Invoque o subagente `prompt-critico` (guardado — veja abaixo) passando o rascunho e os
casos de teste da Fase 1. Ele tenta quebrar o prompt e devolve, por caso, se e como
quebrou. Sintetize os achados, itere o rascunho, repita — no máximo ~3 rodadas antes de
reavaliar se o problema é o prompt ou o critério de sucesso da Fase 0. Registre o que
mudou e por qual caso/furo em cada rodada.

## Fase 5 — Checklist de hardening

Antes do portão, confirme:

- [ ] Temperatura definida via um gate/config central, não hardcoded na chamada
- [ ] Formato de saída tem schema explícito se algo vai fazer parsing downstream
- [ ] Decisão explícita fail-open vs. fail-closed para qualquer guardrail/classificador
- [ ] Pelo menos um exemplo negativo cobrindo a categoria mais ambígua
- [ ] Se o prompt tem regras numeradas, cada uma é rastreável a um motivo/caso real (não
      regra "por via das dúvidas")

Leia `references/temperatura_e_hardening.md` para o detalhe de cada item.

## Fase 6 — PORTÃO: aprovação obrigatória (STOP)

Apresente o prompt final, os resultados dos casos de teste, e o checklist marcado. Pare.
`AskUserQuestion`:

- **Aprovar** → Fase 7.
- **Mais uma rodada de crítica** → volta à Fase 4.
- **Rejeitar e redesenhar** → volta à Fase 2.

Isso vale mesmo em modo exploratório — a diferença é que, em exploratório, itens do
checklist da Fase 5 podem ficar marcados como "pendente para quando virar produção" em
vez de bloquear a aprovação.

## Fase 7 — Entrega

Grave/edite o prompt no arquivo-alvo. Se for um prompt novo em produção, indique onde o
gate de temperatura deveria viver (config centralizada, não a chamada individual). Se o
projeto não tem harness de eval, recomende manter um changelog leve do prompt — e, se uma
correção futura vier a mexer nele, aponte para a skill `sdd` e a disciplina "corrigir a
classe, não o caso".

## Subagente: `prompt-critico`

Guardado — exige um bloco `PROMPT_CANDIDATO:` e `CASOS_DE_TESTE:` no prompt de invocação,
senão se recusa a rodar. Simula a resposta mais provável do prompt para cada caso, tenta
pelo menos 2 ataques adversariais além dos já listados, e devolve por caso se encontrou
quebra, como, e a severidade. **Não propõe a correção** — quem decide o que mudar é quem
orquestra esta skill, com base no achado.

## Modos de falha

| Sintoma | Causa | Correção |
|---|---|---|
| Prompt aprovado quebra em produção com input real | Casos de teste da Fase 1 não cobriam a classe de input que apareceu depois | Volte à Fase 1, adicione o caso, rode a Fase 4 de novo — não remende o prompt em produção sem atualizar o teste |
| Regra "não faça X" é ignorada pelo modelo | Regra negativa/vaga sem exemplo positivo do comportamento certo, ou não é numerada/destacada | Reescreva como regra numerada + exemplo positivo do comportamento esperado |
| Saída bate com o schema só às vezes | Formato solto (prosa) em vez de schema forçado + parsing determinístico | Force schema e mova cálculo propenso a erro para código, não para o LLM |
| Temperatura alta reaparece depois de uma refatoração | Temperatura hardcoded na chamada em vez de gate central | Centralize num objeto de config imutável |
| Iteração nunca converge | Critério de sucesso da Fase 0 nunca foi explicitado | Volte à Fase 0 e escreva critério objetivo antes de continuar iterando |
| `prompt-critico` só acha os mesmos 2 furos óbvios | Poucos casos de teste / falta caso adversarial de verdade | Fase 1: adicione casos adversariais explícitos, não só casos felizes |
| Few-shot só tem exemplos positivos | Fase 3 pulou a exigência de exemplo negativo | Adicione ao menos 1 exemplo negativo por categoria ambígua |

## Cross-skill

Se a mudança de prompt é uma decisão arquiteturalmente difícil de reverter (ex.: trocar
zero-shot por tool-use agentic, mudar de classificador único para roteamento em
camadas), considere registrar via skill `sdd` (trilha ADR). Se o prompt em questão é o
de um agente **verificador**, a Fase 3 deve incluir explicitamente um exemplo negativo de
"o que conta como aprovado incorretamente".

## Recursos

| Arquivo | Ler quando |
|---|---|
| `references/neste_projeto.md` | Fase 0, sempre que o prompt for do robô |
| `references/anatomia_e_vocabulario.md` | Fase 2 |
| `references/tecnicas_ladder.md` | Fase 2 |
| `references/tecnicas_avancadas.md` | Fase 2, quando o caso exige raciocínio complexo |
| `references/padroes_de_producao.md` | Fase 3 |
| `references/temperatura_e_hardening.md` | Fase 5 |

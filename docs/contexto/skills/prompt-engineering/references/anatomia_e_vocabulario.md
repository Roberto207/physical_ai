# Anatomia de um prompt + vocabulário padrão

## As 6 partes (use as que a tarefa pedir, nem todo prompt precisa das 6)

| Parte | Pergunta que responde | Exemplo |
|---|---|---|
| **Role** (papel) | Quem o modelo está simulando? | "Você é um revisor de contratos sênior." |
| **Context** (contexto) | Que informação de fundo o modelo precisa? | Os trechos recuperados, o histórico da conversa |
| **Task** (tarefa) | O que exatamente fazer com o contexto? | "Extraia a data de vigência e o valor do contrato." |
| **Format** (formato) | Como a resposta deve ser estruturada? | JSON com campos nomeados, uma única palavra, markdown |
| **Examples** (exemplos) | Few-shot — o que uma resposta boa (e ruim) parece? | Ver `tecnicas_ladder.md` |
| **Constraints/Tone** (restrições/tom) | O que evitar? Qual registro? | "Nunca invente uma cláusula que não está no texto." |

## Por que clareza simples bate complexidade impressionante

LLMs preveem a partir de padrões da distribuição de treino — instruções em linguagem
comum, direta, sem ambiguidade, ativam esses padrões de forma mais confiável do que
prompts "espertos" ou rebuscados. Se a instrução parece complicada de ler para você,
provavelmente é ambígua para o modelo também.

## Anti-padrões (tabela de reconhecimento rápido)

| Anti-padrão | Sintoma | Correção |
|---|---|---|
| Parede de texto | Uma instrução gigante sem estrutura, sem headers/listas | Quebre em seções nomeadas (Role/Context/Task/...) |
| Instruções conflitantes | Duas regras que se contradizem em casos-limite | Rode um caso-limite mentalmente antes de finalizar; se conflitar, priorize explicitamente uma sobre a outra |
| Ambiguidade aberta | "Responda de forma apropriada" sem definir o que é apropriado | Substitua por critério objetivo ou exemplo concreto |
| Contexto irrelevante | Informação de fundo que não afeta a tarefa, só consome tokens e distrai | Corte — cada frase do contexto deve ser usada pela tarefa |

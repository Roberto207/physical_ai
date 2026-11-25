# Spec leve em prosa — o template default

Formato para a maioria das mudanças (bugs, ajustes, features pequenas/contidas):
informal, mas nunca vago. É a trilha **default**
da skill `sdd`: use-a a menos que a mudança seja arquiteturalmente cara de reverter (aí é
ADR) ou seja uma feature grande/greenfield com escopo ainda nebuloso (aí é pipeline
completo).

## Template — feature/ajuste (não-bug)

```markdown
# Objetivo

<uma frase: o que esta mudança entrega>

# Contexto

<por que isso está sendo pedido agora — narre como um pedido real, não uma ata formal>
```

Se a mudança envolve dar um papel/persona específico ao agente que vai implementar
(comum quando a tarefa pede uma lente especializada, ex. "analise a arquitetura como
faria um DBA"), adicione:

```markdown
# Persona e objetivo

Você é <papel>. Seu objetivo é <tarefa>, dividido em:
- <foco 1>
- <foco 2>
```

## Template — bug

```markdown
# Objetivo
# Contexto

## Bug: <sintoma observável> — <causa raiz em uma linha>

### Causa raiz

<evidência concreta: arquivo:linha, valor medido, tabela de casos reais se ajudar a
provar o padrão. Nunca uma causa raiz "provável" sem ter lido o código.>

### A classe do problema

<esta falha específica é uma instância de que classe mais ampla de bug? Isso é o que
separa "consertei o sintoma" de "consertei a causa" — cite a regra de governança do
projeto se ele tiver uma (ex.: uma seção do AGENTES.md).>

### Fix proposto

<sketch de código real, não só descrição em prosa — regex, assinatura de função,
diff conceitual>

### Passos para resolver (checklist)

- [ ] <passo 1>
- [ ] <passo 2>
- [ ] rodar o eval set / suite de testes relevante
- [ ] considerar se isso merece virar um ADR (a correção muda uma decisão arquitetural?)
```

## Template de fechamento — quando a spec é implementada

Depois que a spec vira código, use esta estrutura no documento da tarefa
(`docs/tarefas/AAAA-MM-DD-<nome>.md`). Ele registra por que o código é assim:

```markdown
# <Título>

## Problema

<o que estava errado/faltando, 2-3 frases>

## Solução implementada

<o que foi feito, com trecho de código relevante e, se ajudar, um diagrama ASCII do
fluxo de dados>

## Onde está implementado

<arquivo:linha ou lista de arquivos>

## Comportamento

<o que muda do ponto de vista de quem usa o sistema>

## O que NÃO mudou

<declaração explícita de não-regressão — o que continua exatamente igual, para quem
for revisitar este código depois não precisar reconstruir isso por inferência>

## Verificação

<comandos bash reais para re-validar que a correção continua funcionando>
```

## Regra de ouro desta trilha

Uma spec leve não é "menos rigorosa" — é rigorosa sobre menos coisas. Ela ainda exige
causa raiz investigada (não suposta), um fix concreto (não vago), e um checklist de
verificação. O que ela dispensa é o aparato formal (EARS, ADR, três documentos
separados) quando o escopo não justifica.

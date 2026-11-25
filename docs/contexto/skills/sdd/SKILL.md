---
name: sdd
description: >
  Use sempre que o usuário pedir para especificar, documentar ou planejar uma mudança de
  código antes de implementar — por exemplo "cria uma spec para isso", "documenta essa
  decisão de arquitetura", "isso merece um ADR?", "escreve os requisitos dessa feature",
  "define o critério de aceite", "vamos fazer um brainstorm antes de codar", "isso é
  greenfield ou brownfield?", ou qualquer pedido de Spec-Driven Development (SDD) /
  engenharia de requisitos antes de gerar código. Cobre desde um bug pequeno até uma
  feature grande — a skill decide o nível de rigor certo (spec leve em prosa, ADR, ou
  pipeline completo de 5 fases), nunca impõe sempre o mesmo tamanho de processo. SEMPRE
  resolve na Fase 0 qual nível de rigor usar e PARA no portão de aprovação antes de
  escrever a versão final da spec/ADR ou de gerar qualquer código a partir dela — nunca
  assume o nível de rigor nem pula a aprovação.
argument-hint: '"<mudança ou decisão>" [--modo leve|adr|completo] [--concluir <spec>]'
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "AskUserQuestion", "Agent"]
---

# SDD — Spec-Driven Development com rigor adaptativo

Esta skill conduz o fluxo de "escrever antes de codar": desde uma spec leve em prosa para
um bug ou ajuste pequeno, até um ADR para uma decisão difícil de reverter, até o pipeline
completo Brainstorm→Define→Design→Build→Ship para uma feature grande ou greenfield.
**O nível de rigor nunca é assumido — é sempre decidido explicitamente na Fase 0, e a
versão final de qualquer artefato só é gravada depois de um portão de aprovação.**

O problema que SDD resolve: o padrão "500/50/0" — o agente gera 500 linhas, você entende
50, mantém 0. Uma spec é o contrato entre intenção e implementação que evita isso. Mas
spec não é sinônimo de burocracia: a maioria das mudanças cabe numa spec de uma página em
prosa, e o ADR formal fica só para decisões que doeriam reverter depois. *Combine o processo ao tamanho real do
problema — um processo pesado demais para uma mudança pequena é tão ruim quanto nenhum
processo para uma mudança grande.*

## Quando NÃO usar

Mudança trivial e óbvia (typo, rename, formatação) — implemente direto. Pergunta factual
sobre o código — responda direto, não abra spec para investigar.

## Fase 0 — Triagem e roteamento

1. **Siga a convenção deste projeto** antes de qualquer coisa. Leia
   `docs/contexto/AGENTES.md` e olhe o que já existe:
   - specs em `specs/<nome>/` (leve: um `SPEC.md`; completa: `BRAINSTORM.md`, `DEFINE.md`,
     `DESIGN.md` na mesma pasta);
   - ADRs em `docs/decisoes/ADR-NNN-<nome>.md`, com índice em `docs/decisoes/README.md`;
   - um documento por tarefa em `docs/tarefas/`.
   Em outro projeto, procure `specs/`, uma pasta de decisões e o `CLAUDE.md`, e siga o
   padrão local.
2. Classifique a mudança com `AskUserQuestion` entre:
   - **Spec leve** — bug, ajuste pequeno, feature contida (default).
   - **ADR** — decisão arquitetural difícil/cara de reverter (troca de stack, mudança de
     modelo de dados, mudança de estratégia de segurança).
   - **Pipeline completo** — feature grande, greenfield, ou algo com escopo ainda
     nebuloso que precisa de brainstorm antes de virar requisito.
   - **"Não sei, me ajuda a decidir"** — dispara perguntas diagnósticas: é bug ou feature
     nova? a decisão seria cara/difícil de desfazer depois? o escopo já está claro ou
     ainda é uma ideia solta?
3. Se `--modo` foi passado via `$ARGUMENTS`, use-o e pule a pergunta — mas ainda confirme
   em uma linha antes de prosseguir ("Vou tratar isso como ADR, certo?").
4. Se `--concluir <spec>` foi passado, pule para a Fase 5 direto (fechamento de uma spec
   leve já implementada).

## Fase 1 — Levantamento de contexto

Nunca escreva o artefato sem evidência concreta:

- **Bug**: leia o stack trace/sintoma relatado, rode `git log`/`git blame` no arquivo
  afetado, isole a causa raiz com evidência real (arquivo:linha, valor observado). Nunca
  invente uma causa raiz plausível sem ter lido o código.
- **Feature**: leia o código adjacente, `docs/contexto/AGENTES.md` e
  `docs/contexto/stack.md` (convenções, stack, regras já declaradas).
- **ADR**: rode `ls docs/decisoes/ADR-*.md` para não colidir numeração, e leia 1-2 ADRs
  existentes para casar o tom/nível de detalhe.
- **Qualquer trilha que envolva o robô, o ROS ou o Nav2**: confirme o comportamento na
  documentação oficial e cite a página na spec.

## Fase 2 — Redigir o artefato

Ramifica pela trilha escolhida na Fase 0.

### Trilha leve (default)

Leia `references/spec_leve_prosa.md`. Estrutura mínima:

```
# Objetivo
# Contexto
```

Para bug, adicione:

```
## Bug: <sintoma> — <causa raiz em uma linha>
### Causa raiz
   (evidência: arquivo:linha, valor observado)
### A classe do problema
   (esta falha é uma instância de que classe mais ampla? cite a regra de governança
   do projeto se existir, ex. uma seção do AGENTES.md)
### Fix proposto
   (sketch de código, não só descrição)
### Passos para resolver (checklist)
   - [ ] ...
   - [ ] rodar o eval set / suite de testes relevante
   - [ ] considerar se isso vira um ADR
```

### Trilha ADR

Leia `references/adr_template.md`. Estrutura fixa:

```
# ADR-NNN: <título>
**Status:** Proposto | Aceito | Substituído por ADR-XXX
**Data:** <AAAA-MM-DD>

## Contexto
## Decisão
## Alternativas Consideradas
   | Alternativa | Razão da rejeição |
## Consequências
   ### Positivas
   ### Negativas
   ### Mitigação
```

**Regra dura: máximo 200 palavras por ADR.** Se a decisão não cabe, é sinal de que são
duas decisões — divida em dois ADRs em vez de inflar um.

### Trilha completa (feature grande / greenfield)

Três sub-fases, cada uma com modo de pensamento e artefato próprios:

- **2a. Brainstorm** (divergente) → `BRAINSTORM.md`: problema percebido, hipóteses,
  riscos. Não convirja ainda — o objetivo é mapear o espaço, não escolher.
- **2b. Define** (convergente) → `DEFINE.md`: requisitos em **sintaxe EARS** (leia
  `references/ears.md` para os 5 moldes — Ubiquitous/Event-driven/State-driven/
  Unwanted/Optional) e uma lista explícita DEVE/NÃO DEVE. Depois de escrito, considere
  invocar o subagente `sdd-ears-critico` (veja "Subagente" abaixo) para atacar
  ambiguidade/testabilidade de cada critério antes do portão.
- **2c. Design** (arquitetural) → `DESIGN.md`: arquitetura proposta cobrindo os 3
  pilares de produção — Identidade, Observabilidade, Rastreabilidade (leia
  `references/pilares_producao.md`). *Um agente que "funciona" é só ~25% do trabalho —
  os outros 75% são esses três pilares.*

## Fase 3 — PORTÃO: aprovação obrigatória (STOP)

Apresente o rascunho completo do artefato (spec leve, ADR, ou o trio Brainstorm/Define/
Design). Pare. Use `AskUserQuestion` com estas opções:

- **Aprovar** — segue para a Fase 4 exatamente como está.
- **Ajustar e reconfirmar** — pede o que mudar, edita, volta a este portão.
- **Rejeitar e refazer** — volta à Fase 2 (ou à Fase 0 se o problema for o nível de
  rigor escolhido).

*Entusiasmo genérico ("bora", "faz sentido", "manda ver") não é aprovação — se a resposta
não confirma o conteúdo específico do artefato, trate como não-aprovado e peça
confirmação item a item.*

## Fase 4 — Build

Grave a versão final do artefato aprovado no caminho correto (`specs/<nome>/` ou
`docs/decisoes/`). Na trilha completa,
implemente o código **exatamente conforme o `DESIGN.md` aprovado** e produza um
`BUILD_REPORT.md` (o que foi implementado, o que ficou de fora e por quê, como verificar).
Nunca expanda o escopo além do que foi aprovado no portão — se surgir a tentação, isso é
uma nova spec, não um adendo silencioso a esta.

**Robô físico:** aprovar a spec não autoriza mover nem configurar o robô. Cada ação crítica
continua pedindo permissão na hora (`docs/contexto/AGENTES.md`, seção 1), e o critério é
verificado no simulador antes do hardware.

## Fase 5 — Fechar / Ship

- **Leve**: atualize a linha `**Status:**` do `SPEC.md` (executada em, relatório em).
- **ADR**: atualize o índice em `docs/decisoes/README.md`.
- **Completa**: escreva `SHIPPED.md` fechando o ciclo. Se a retro apontar um problema
  novo, isso vira um `BRAINSTORM.md` novo, não um remendo neste.
- **Em todas**: crie `docs/tarefas/AAAA-MM-DD-<nome>.md` (o que foi feito, em qual
  arquivo, para que serve, como foi verificado e o que não foi), acrescente a linha na
  tabela de `docs/tarefas/README.md` e rode `python3 infra/ferramentas/checar_caminhos.py`.

## Subagente: `sdd-ears-critico` (opcional, só na trilha completa)

Invocado depois de escrever `DEFINE.md`, a menos que `--sem-critico-ears` tenha sido
passado. Ataca testabilidade e ambiguidade de cada critério de aceite. Chame com um bloco
`CRITERIOS:` contendo as linhas DEVE/NÃO DEVE do `DEFINE.md` — sem isso o subagente se
recusa a rodar (é um componente interno guardado, não um agente de propósito geral).

## Modos de falha

| Sintoma | Causa | Correção |
|---|---|---|
| Skill sempre propõe pipeline completo mesmo para bug pequeno | Fase 0 pulada ou critério de roteamento ignorado | Volte à Fase 0, force a triagem explícita |
| ADR vira ensaio, passa de 200 palavras | Contexto/Decisão não foi separado de Consequências | Corte para o essencial; mova detalhe para a spec leve associada ou divida em dois ADRs |
| Spec de bug cita só o sintoma, não a causa raiz | Fase 1 pulada, foi direto pro template | Volte à Fase 1 e investigue com Read/Grep/Bash antes de redigir |
| Critério de aceite em DEFINE.md é vago/não testável | EARS não foi aplicado (frase livre em vez de um dos 5 moldes) | Reescreva usando os moldes EARS; rode `sdd-ears-critico` |
| Usuário aprovou com entusiasmo genérico sem ler o artefato | Portão tratou "bora"/"faz sentido" como aprovação | Trate como não-aprovação; peça confirmação item a item |
| Numeração de ADR colide com um já existente | Não escaneou docs/decisoes/ antes de nomear o arquivo | Sempre `ls docs/decisoes/ADR-*.md` antes de atribuir NNN |
| Skill ignora convenção já estabelecida do projeto e impõe requirements.md/design.md formais num projeto que já usa prosa leve | Fase 0 não detectou o padrão existente | Sempre detectar specs e decisões existentes primeiro e seguir o padrão do projeto |

## Se a implementação exigir automação

Se o artefato aprovado exige configurar hooks, permissões, `settings.json`, ou qualquer
automação recorrente, a Fase 4 **não configura isso diretamente**. Recomende a skill
`update-config` para configuração estática, ou `schedule`/`loop` para automação
recorrente — e, se a automação for não-trivial (mais de um passo, ou envolve autonomia
sem supervisão) e a skill `loop-engineering` estiver instalada, sugira rodá-la primeiro
para desenhar o loop antes de configurá-lo.

## Recursos

| Arquivo | Ler quando |
|---|---|
| `references/ears.md` | Fase 2, trilha completa (sub-fase Define) |
| `references/adr_template.md` | Fase 2, trilha ADR |
| `references/spec_leve_prosa.md` | Fase 2, trilha leve; e Fase 5 ao fechar |
| `references/pilares_producao.md` | Fase 2, trilha completa (sub-fase Design) |
| `references/frameworks_prior_art.md` | Só se o usuário pedir comparação com Spec Kit/Kiro/BMAD/outras ferramentas de mercado |

# Paisagem de ferramentas SDD (2026) — prior art, não obrigatório

Leia isto só se o usuário pedir explicitamente para comparar com ferramentas de mercado,
ou quiser justificar por que a skill `sdd` usa o processo que usa. Não é necessário para
executar o fluxo normal da skill.

## Decisão greenfield vs. brownfield

| | Greenfield (projeto novo) | Brownfield (código existente) |
|---|---|---|
| Ponto de partida | Spec vem antes de qualquer linha de código | Spec precisa primeiro descrever o comportamento atual, depois o desejado |
| Risco principal | Especificar demais antes de validar a ideia | Especificar sem entender debt/acoplamento existente |
| Ferramenta mais alinhada | GitHub Spec Kit, Kiro | OpenSpec (brownfield-first), AgentSpec |

## Ferramentas

- **GitHub Spec Kit** — workflow via slash commands: `/constitution` (regras do
  projeto) → `/specify` (requisitos) → `/clarify` (resolve ambiguidade) → `/plan`
  (arquitetura) → `/tasks` (quebra em tarefas) → `/implement`. Mapeia quase 1:1 no
  pipeline Brainstorm→Define→Design→Build→Ship desta skill, com nomes diferentes.

- **Kiro** (AWS) — produz três artefatos por feature: `requirements.md` (em sintaxe
  EARS), `design.md`, `tasks.md`. É a origem direta do template EARS usado na sub-fase
  Define desta skill.

- **BMAD-METHOD** — pipeline de agentes-persona: Analyst → PM → Architect → Scrum
  Master → Dev → QA, cada um com um papel fixo. Mais pesado que o necessário para a
  maioria das mudanças, mas é uma referência útil se o projeto quiser formalizar quem
  (humano ou agente) é responsável por cada fase.

- **GSD, OpenSpec, AgentSpec (Luan Moreno Medeiros Maciel), Superpowers** — variações
  menores no mesmo espaço; OpenSpec se destaca por ser explicitamente brownfield-first
  (assume que a maior parte do trabalho real é em código existente, não greenfield).

## Por que esta skill não adota nenhuma ferramenta específica 1:1

A skill parte da spec leve em prosa, que cobre a maioria das mudanças, e empresta o
vocabulário/rigor dessas ferramentas (EARS, ADR, pipeline de fases) só quando o tamanho
da mudança justifica.

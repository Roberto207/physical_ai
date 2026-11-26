# Skills e subagentes do Claude Code neste projeto

Uma **skill** é uma pasta com um `SKILL.md` (instruções) e arquivos de apoio que o Claude Code carrega quando o pedido combina com a `description` dela. As desta pasta valem **só neste repositório**, carregam sem instalação e chegam por `git pull`.

| Item | Para que serve |
|---|---|
| `skills/sdd/` | Escrever a spec ou o ADR antes de codar, com portão de aprovação. É o formato de `specs/` |
| `skills/economia-agentes/` | Decidir se uma tarefa vai para subagente; proíbe subagente de tocar o robô |
| `skills/prompt-engineering/` | Escrever e testar prompts com casos adversariais (missão da LLM) |
| `skills/preflight-robo/` | Conferir PC, rede, robô e Nav2 antes de a patrulha ou o LLM moverem o robô (usa `scripts/checar.sh`) |
| `agents/prompt-critico.md` | Subagente usado pela `prompt-engineering` para tentar quebrar o prompt |
| `agents/sdd-ears-critico.md` | Subagente usado pela `sdd` para atacar critérios de aceite ambíguos |

## Conferir

Abra uma sessão nova do `claude` na raiz do repositório e digite `/`: as quatro skills precisam aparecer na lista. Documentação oficial: https://code.claude.com/docs/en/skills e https://code.claude.com/docs/en/sub-agents

## Atualizar

Edite aqui e faça o commit. As três primeiras foram adaptadas em 25/11 das skills pessoais do Roberto. Se existir uma skill pessoal de mesmo nome em `~/.claude/skills/`, confira qual está sendo usada.

O repositório é público: nada de senha, token ou informação de outros projetos.

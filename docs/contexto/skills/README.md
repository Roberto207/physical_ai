# Skills do Claude Code para o PC do laboratório

Uma **skill** é uma pasta com um `SKILL.md` (instruções) e arquivos de apoio que o Claude Code carrega quando o pedido combina com a `description` dela. Esta pasta serve só de **transporte pelo git**: o Claude Code não lê skills daqui, é preciso instalar.

## O que tem aqui

| Item | Para que serve | Instala em |
|---|---|---|
| `sdd/` | Escrever a spec ou o ADR antes de codar, com portão de aprovação. É o formato de `specs/` | `~/.claude/skills/` |
| `economia-agentes/` | Decidir se uma tarefa vai para subagente, com qual modelo, e proibir subagente de tocar o robô | `~/.claude/skills/` |
| `prompt-engineering/` | Escrever e testar prompts com casos adversariais antes de aprovar (missão da LLM) | `~/.claude/skills/` |
| `agentes/prompt-critico.md` | Subagente usado pela `prompt-engineering` para tentar quebrar o prompt | `~/.claude/agents/` |
| `agentes/sdd-ears-critico.md` | Subagente usado pela `sdd` na trilha completa para atacar critérios de aceite ambíguos | `~/.claude/agents/` |

## Instalar

Na raiz do repositório, no PC do laboratório:

```bash
# Antes: veja se já existe algo com o mesmo nome, porque o cp sobrescreve
ls ~/.claude/skills ~/.claude/agents

mkdir -p ~/.claude/skills ~/.claude/agents
cp -r docs/contexto/skills/{sdd,economia-agentes,prompt-engineering} ~/.claude/skills/
cp docs/contexto/skills/agentes/*.md ~/.claude/agents/
```

`~/.claude/` vale para todos os projetos do usuário logado. Se o usuário do PC for compartilhado, use `.claude/skills/` e `.claude/agents/` na raiz do repositório: valem só neste projeto.

## Conferir

Abra uma sessão nova do `claude` na raiz do repositório e digite `/`: `sdd`, `economia-agentes` e `prompt-engineering` precisam aparecer na lista. Documentação oficial: https://code.claude.com/docs/en/skills e https://code.claude.com/docs/en/sub-agents

## Atualizar

As cópias daqui foram **adaptadas** em 2026-11-25 a partir das skills pessoais do Roberto: saíram referências a outros projetos e caminhos do notebook, e entraram as convenções deste repositório. Edite aqui, faça o commit, e no PC do laboratório rode `git pull` e os comandos de instalação de novo.

O repositório é público: não coloque nestas pastas senha, token, nem informação de outros projetos.

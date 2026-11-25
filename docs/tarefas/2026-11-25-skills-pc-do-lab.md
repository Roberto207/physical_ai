# Skills do Claude Code para o PC do laboratório (2026-11-25)

As skills `sdd`, `economia-agentes` e `prompt-engineering`, mais os subagentes `sdd-ears-critico` e `prompt-critico`, estão em `docs/contexto/skills/`, adaptadas a este repositório. O PC do laboratório recebe por `git pull` e instala com os comandos de `docs/contexto/skills/README.md`.

## O que foi feito

| Arquivo | O que é | Mudança em relação à skill original |
|---|---|---|
| `docs/contexto/skills/sdd/` | Spec ou ADR antes do código | Usa `specs/<nome>/`, `docs/decisoes/` e `docs/tarefas/`; exemplos trocados para patrulha, Nav2 e LLM; aprovar spec não autoriza mover o robô |
| `docs/contexto/skills/economia-agentes/` | Quando e como delegar a subagentes | Tabela de roteamento só com agentes que existem no PC do lab; subagente não toca o robô; simulação nunca em paralelo; saiu a referência de transcrição de vídeo |
| `docs/contexto/skills/agentes/sdd-ears-critico.md` | Crítico dos critérios de aceite | Cópia sem mudança |
| `docs/contexto/skills/prompt-engineering/` | Escrever e testar prompts | Saiu o arquivo de padrões de outro projeto e entrou `references/padroes_de_producao.md`, com exemplos da LLM no robô; prompt que move o robô é sempre tratado como produção |
| `docs/contexto/skills/agentes/prompt-critico.md` | Crítico adversarial do prompt | Cópia sem mudança |
| `docs/contexto/skills/README.md` | Instalação e atualização | Novo |
| `docs/contexto/AGENTES.md` | Índice das regras | Uma linha apontando para o README acima |

O repositório é público no GitHub. Por isso saíram das cópias as referências a outros projetos do Roberto e os caminhos do notebook.

## Para que serve

O Claude Code do PC do laboratório passa a seguir o mesmo processo do notebook: spec com portão de aprovação e controle de gasto do plano ao delegar.

## Como foi verificado

- Busca nas cópias por nomes de outros projetos, `docs/decisions` e caminhos `/home/`: nenhuma ocorrência.
- `python3 infra/ferramentas/checar_caminhos.py` rodado neste notebook.

## O que não foi verificado

- Instalação e execução das skills no PC do laboratório.
- Os dois links da documentação do Claude Code citados no README não foram abertos nesta tarefa.

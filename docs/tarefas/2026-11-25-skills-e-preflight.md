# Skills em `.claude/` e skill `preflight-robo`

**Data:** 2026-11-25

**Resposta direta:** as três skills e os dois subagentes que chegaram pelo git passaram a valer neste PC, em `.claude/`, com ajustes para este ambiente. A skill `preflight-robo` foi implementada conforme `specs/preflight-robo/SPEC.md`, testada só com comandos simulados; falta validar no robô.

## Skills movidas

`docs/contexto/skills/` deixou de existir (era só transporte pelo git). Ajustes:

| Skill | Ajuste |
|---|---|
| `sdd` | Como rodar testes neste PC (sem `pytest` no host); saíram menções a uma skill não instalada |
| `economia-agentes` | Subagente só quando o usuário pede; avaliação sem escrita no repositório e sem rede para o robô |
| `prompt-engineering` | Novo `references/neste_projeto.md`, com o modelo, os arquivos da LLM e como medir |
| Subagentes | Sem mudança |

## Skill `preflight-robo`

| Arquivo | O que faz |
|---|---|
| `.claude/skills/preflight-robo/scripts/checar.sh` | Leituras das fases A (A1 a A8), C (C1 a C3) e C4; grava o relatório em `workspace/logs/` |
| `.claude/skills/preflight-robo/SKILL.md` | Ordem, pedidos de OK, confirmações do operador e veredito |

Também: a menção à V5 em `specs/patrol-inf/DESIGN.md` passou a registrar que ela foi declarada aprovada pelo Roberto, sem registro da medição.

## Como foi verificado

- `bash -n`; critério P3 (a única linha que casa é a que detecta o controle manual em A2).
- Cópia do script num diretório temporário, com `lab.sh`, `docker`, `ping` e `sleep` falsos: 17 cenários (tudo certo, robô sem ping, imagem errada, concorrentes, aviso de rede, fora da doca, bateria baixa ou `nan`, nó inativo, falha no log, Nav2 ausente, códigos do C4), todos com o resultado esperado.
- `checar_caminhos.py`.

## O que não foi verificado

- Nenhuma checagem rodou contra o robô: havia uma sessão do operador em andamento. Os formatos reais de `get_state`, `echo --field` e dos logs podem diferir dos simulados.
- `shellcheck` não está instalado.
- O carregamento das skills numa sessão nova.

## Efeito prático

Numa sessão nova do `claude` na raiz, pedir o preflight (ou `/preflight-robo`) antes de rodar a patrulha.

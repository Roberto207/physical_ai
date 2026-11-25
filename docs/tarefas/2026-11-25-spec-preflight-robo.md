# Spec da skill `preflight-robo` (2026-11-25)

A spec está em `specs/preflight-robo/SPEC.md`, aprovada pelo Roberto. A skill ainda não existe: será criada no PC do laboratório, onde os comandos podem ser testados com o robô.

## O que foi feito

| Arquivo | O que é |
|---|---|
| `specs/preflight-robo/SPEC.md` | Checagens antes de mover o robô, o que a skill pode fazer sem OK, com OK e nunca, passos de implementação e critérios de pronto |
| `docs/contexto/AGENTES.md` | A spec entrou na lista da seção 7 |

Decisões do Roberto: spec leve; a skill sobe serviços no PC com OK e não mexe no robô; V5 considerada aprovada; só a patrulha oficial.

Depois da aprovação houve dois ajustes de forma: a linha de status e o comando do P3, que saiu da tabela para um bloco de código, porque o `\|` da tabela mudaria o sentido do `grep` se copiado do texto cru.

## Para que serve

No laboratório, abrir o Claude Code na raiz do repositório e pedir a implementação de `specs/preflight-robo/SPEC.md`.

## Como foi verificado

As checagens foram tiradas de `workspace/patrulha_oficial/`, de `infra/docker/lab.sh` e dos documentos de tarefa de 21 e 23/11. `python3 infra/ferramentas/checar_caminhos.py` rodado no notebook.

## O que não foi verificado

- Nenhum comando da spec foi executado nesta tarefa. A seção 8 da spec lista as dúvidas a tirar no laboratório.
- Os links da documentação oficial citados vêm dos documentos do repositório e não foram reabertos hoje.
- A V5 não tem a medição registrada: a aprovação é informação do Roberto.

## Observado e não corrigido

A mensagem de `REDE REPROVADA` do `infra/docker/lab.sh` apontava para um documento que não existia. O commit `88450bd` corrigiu.

## Ajustes depois do merge

O push encontrou dois commits novos no remoto (`88450bd` e `b320c20`), que reorganizaram pastas. Mudanças na spec:

| Trecho | Ajuste |
|---|---|
| A8 | O `patrol_loop.py` saiu de `upstream/` para `workspace/patrulha_oficial/` |
| Passo 1 | Os avisos da V5 já tinham saído; resta uma menção em `specs/patrol-inf/DESIGN.md` |
| Seção 8 | Saiu a dúvida sobre memória compartilhada: o documento de 23/11 passou a descartar a hipótese, porque os contêineres usam UDPv4 |

A spec também entrou na tabela de `specs/README.md`.

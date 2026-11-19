# Tarefa: enxugamento e organização do projeto

**Data:** 2026-11-19
**Spec:** `specs/enxugamento/SPEC.md` (aprovada em 2026-11-18, propostas P1, P2 e P3 aprovadas)
**Situação:** executada de E1 a E6, com commits locais (sem push). Os critérios C1 a C8 passam, com duas conferências que o notebook não consegue fazer (seção 4).

## 1. Resposta direta

O contexto que estava espalhado em seis lugares agora está em um `docs/` só, com o `README.md` na raiz como porta de entrada. A pasta `contexto/` não existe mais. O `progresso/` (fora do git) foi apagado com o ok do Roberto, depois de o essencial virar `docs/historico/resultados-jazzy.md`. O `estudo/` saiu do git e continua no disco. Três arquivos de código sem uso saíram. Um checador de caminhos novo roda no CI e reprova documento vivo que cita arquivo inexistente.

## 2. O que mudou, por etapa

| Etapa | Commit | O que foi feito |
|---|---|---|
| E1 | `docs: resumo dos resultados Jazzy` | Escrito `docs/historico/resultados-jazzy.md` a partir do `testes.md`, `patrol-loop.md` e `proximos-degraus.md`: medições de 5 e 9/nov, os três defeitos do `patrol_loop` e onde cada um foi resolvido, os 11 cenários L1 de 12 e 13/nov (veredito, número, RAM) e as pendências fechadas |
| E2 | `docs: estrutura única em docs/` | `git mv` de `contexto/`, `como_rodar.md`, `docs/acesso-ao-robo-por-cabo.md` e `docs/registro-de-mudancas.md` para `docs/contexto/`, `docs/guias/`, `docs/decisoes/` e `docs/historico/`. Fundidos: `projeto.md` (briefing, escopo e missões) e `maquinas.md` (máquina do Roberto mais os fatos do PC do lab e do robô, hoje em `specs/patrol-inf/kit-de-campo.md` e `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md`). `stack.md` atualizado para Humble, Fortress, `lab_tb4` e loopback vendorizado. `pendencias.md` ficou só com o que está aberto. `docs/decisoes/README.md` virou o índice: ADRs no topo, decisões antigas embaixo |
| E3 | `docs: README e AGENTES (registro por tarefa, P1)` | `README.md` novo. `AGENTES.md` reescrito: seção 3 com o ADR-001 e o ADR-002, seção 4 com o limite de 7,4 GiB só para o notebook, seção 5 sem analogia, seção 6 com a regra do registro novo, seção 7 com a tabela "onde achar" nova. `docs/tarefas/README.md` com a tabela data, tarefa, documento (P1) |
| E4 | `chore: código sem uso ...` | Saíram `workspace/exemplos/decisao_patrulha.py`, o `test_decisao_patrulha.py` e `config/warehouse_original.yaml` do `patrulha_tb4` (P2: o teste parametrizado perdeu esse caso). O `decisao.py` cita o exemplo pela tag `jazzy-final`. O `teste_l1.sh` grava em `workspace/logs/l1/<data>-<cenario>/` |
| E5 | `chore: estudo fora do git` e `chore: progresso/ apagado ...` | `git rm -r --cached estudo` (28 arquivos) e `caminho_estudo_humano.md` movido para dentro de `estudo/`. `progresso/` apagado (1,6 MB, sem volta) e a linha `progresso/` saiu do `.gitignore` |
| E6 | `docs: citações e verificação` | Citações de `contexto/`, `progresso/` e `como_rodar.md` corrigidas em `specs/`, `docs/guias/`, ADR-002 e `workspace/mapas/README.md`. Criado `infra/ferramentas/checar_caminhos.py` (P3) e um passo no job `lint` do `.github/workflows/ci.yml`. `PREVIA.md` removida. Este documento |

## 3. Como o checador de caminhos funciona (P3)

`infra/ferramentas/checar_caminhos.py` (Python puro, sem dependências):

1. Percorre os `.md` do projeto, menos `docs/historico/`, `docs/tarefas/`, `specs/enxugamento/`, `specs/migracao-humble/` e `estudo/`. As duas specs excluídas descrevem arquivos que saem ou mudam de lugar, então citam caminhos que de propósito não existem mais.
2. Remove os blocos de código e, dos trechos entre crases que sobram, separa cada palavra. Fica com as que começam por `docs/`, `infra/`, `specs/` ou `workspace/`.
3. Ignora marcadores (`<...>`, `*`, `...`, `AAAA`) e as saídas que não estão no git (`workspace/logs`, `build`, `install`, `log` do colcon e o mapa `lab.*`, que a spec do kit de campo cita como o que ainda será gerado).
4. Sai com 1 e lista `arquivo: caminho não existe` para cada citação quebrada.

Verificado: passa no estado atual e reprova uma citação falsa colocada de propósito num arquivo temporário (removido depois). Na primeira execução achou 5 citações vivas quebradas além das de `contexto/` e `progresso/` (o `como-rodar.md` apontava para dois arquivos movidos, e o DESIGN da `patrol-inf` para scripts removidos na migração).

## 4. Critérios de pronto

| # | Resultado | Como foi conferido |
|---|---|---|
| C1 | Passa | `git grep` do critério: 0 linhas |
| C2 | Passa | `git ls-files estudo`: 0; `ls estudo/plano`: 11 arquivos |
| C3 | Passa | `test ! -e contexto` |
| C4 | Passa | O `grep` só acha as duas frases que proíbem analogia |
| C5 | Passa | O `README.md` cita `docs/guias/como-rodar.md`, `specs/` e `docs/decisoes/README.md` |
| C6 | Parcial | L0 (comparado com um worktree do commit anterior à E1): `lab_tb4` 17 e 17; `patrulha_tb4` 134 antes e 133 depois (o caso `warehouse_original.yaml` saiu, como a P2 prevê); `exemplos` 19 antes e 11 depois (os 8 testes do exemplo removido). Rastreio: 31 de 31. `docker compose config`: `robo.yaml` e `sim.yaml` válidos. **Não verificados no notebook:** `ruff` e `actionlint` (não estão instalados aqui; rodam no CI) |
| C7 | Passa | `grep` no `teste_l1.sh` acha `workspace/logs/l1` |
| C8 | Passa | `python3 infra/ferramentas/checar_caminhos.py` sai com 0 |

## 5. O que não foi feito e o que fica

- Nada foi enviado ao GitHub: os commits ficam locais até o Roberto publicar. O passo novo do CI só será exercitado depois do push.
- As evidências do L1 de 12 e 13/nov (15 pastas), os logs de 09 e 12/nov, a foto da câmera do Gazebo e o `sensores.py` foram apagados com o `progresso/`. O resumo numérico está em `docs/historico/resultados-jazzy.md`. O `sensores.py` mostrava como assinar os tópicos com QoS `best_effort`; a medição M-GZ precisará de um script equivalente.
- Cada um dos 10 documentos anteriores de `docs/tarefas/` ganhou, logo abaixo do título, a nota de que os caminhos são da época e de que o mapa está no `README.md`. O resto do texto deles não mudou.

## 6. Efeito prático

Quem chega ao projeto (pessoa ou agente) abre o `README.md`, e dali chega ao como-rodar, às regras (`docs/contexto/AGENTES.md`), às decisões e às specs em até 3 leituras. Daqui em diante, mover ou apagar um arquivo citado num documento vivo deixa o job `lint` do CI vermelho. Cada tarefa nova acrescenta uma linha em `docs/tarefas/README.md` e não precisa mais reescrever o que mudou numa segunda tabela.

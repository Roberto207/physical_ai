# PRÉVIA: enxugamento e organização do código e do contexto

**Status:** Prévia, não aprovada. Isto é a lista de pontos anotados, e não uma spec. Vira BRAINSTORM/DEFINE pela skill `/sdd` depois da migração para Humble.
**Data:** 2026-11-18
**Por que depois da migração:** a migração (`specs/migracao-humble/`) reescreve as imagens, os compose, os scripts e boa parte dos comandos dos documentos. Organizar esses textos antes seria fazer o mesmo trabalho duas vezes. O que a migração remover entra aqui como "já feito".

## 1. Regras desatualizadas que os agentes leem

| Ponto | Onde | Problema |
|---|---|---|
| "Explique com uma analogia do dia a dia" | `contexto/AGENTES.md`, seções 5 e 6 | Contradiz a preferência atual do Roberto (sem analogias, explicação técnica). Agentes de outra máquina seguem a regra errada |
| Regras do notebook como regra geral | `contexto/AGENTES.md`, seção 4 | O notebook deixou de simular (2026-11-18). As regras de 7,4 GiB valem para ele, mas não para o PC do lab |
| Simulador leve como principal | `contexto/AGENTES.md`, seção 3 | Substituída pelo ADR-002 |

## 2. Documentos com informação errada ou velha

| Ponto | Onde |
|---|---|
| Caminhos sem `Roberto/` (`~/dev/physical_ai/infra/docker`, `.../workspace/meu_ws/...`) | `como_rodar.md` |
| "124 testes" (são 130) | `como_rodar.md` |
| Itens fechados ou obsoletos misturados com os abertos (`git init`, `warehouse`, Kaggle, The Construct) | `contexto/pendencias.md` |
| Teste de simulação do notebook de 05/11 | `contexto/infra/teste-simulacao-2026-11-05.md`: vira histórico |
| `caminho_estudo_humano.md` com 4 linhas | Raiz de `Roberto/`: é pessoal ou do projeto? |

## 3. Contexto espalhado

Hoje, o que um agente ou um colega precisa ler está em seis lugares: `contexto/`, `docs/`, `docs/tarefas/`, `docs/decisoes/` (novo), `specs/`, `progresso/` (fora do git) e `como_rodar.md`.

Ideias a avaliar:
- Um índice único na raiz de `Roberto/` (README) com "comece por aqui": o que roda, onde está a spec, onde estão as decisões.
- Pendências separadas do histórico: o que está aberto num arquivo, e o que foi resolvido no registro.
- O `registro-de-mudancas.md` (229 linhas) e os `docs/tarefas/` guardam o mesmo histórico em dois formatos. Opção: o registro vira só uma tabela de ponteiros (data, tarefa, link).
- `contexto/projeto/decisoes.md` como índice condensado dos ADRs, e não como lista paralela.

## 4. Código e scripts

| Ponto | Situação |
|---|---|
| `workspace/exemplos/` (`decisao_patrulha.py`, `validar_acao.py` e testes) | A decisão foi superada pelo `patrulha_tb4`. O `validar_acao.py` pode servir à missão do LLM. Decidir: mover, manter ou apagar |
| TST-06 (guarda de RAM do `teste_l1.sh`) | Nasceu para o notebook. No PC do lab, ele é inofensivo. Rever com a spec `patrol-inf` |
| `infra/tools/` | Vazia depois da F3 da migração? Confirmar e remover |
| `run_sim_headless.sh`, `ros.sh`, `treino_leve.sh` | Saem na F4 da migração (já previsto lá) |
| Configs de teste (`warehouse_original.yaml`, L2) | Ainda servem? |

## 5. Imagens e arquivos binários

- As 3 imagens soltas da raiz (`erro_tela.jpeg`, `image.png`, `image copy.png`) já estavam apagadas na árvore de trabalho em 2026-11-18. Falta o commit e, se a foto da tela do robô importar, levá-la para `progresso/evidencias/`.
- `progresso/` e `estudo/` estão fora do git (`.gitignore`), mas os documentos versionados citam caminhos de lá (`progresso/testes.md`, `progresso/evidencias/l1/`). Decidir: versionar só as evidências que os documentos citam, ou tirar as citações.

## 6. Marcas de conflito

- O merge `f1009a4` deixou marcas em `docs/registro-de-mudancas.md` (dois lados para a noite de 16/11) e em `specs/patrol-inf/kit-de-campo.md` (linhas 58 a 70). **Isto entra na F0 da migração**, porque o CI fica vermelho até ser resolvido. A escolha do texto é do Roberto.

## 7. Critério de pronto (proposto)

- Um agente novo acha em menos de 3 leituras: como rodar, a spec em vigor e as decisões.
- Nenhuma regra lida pelos agentes contradiz o CLAUDE.md do Roberto.
- Nenhum script ou documento cita um arquivo que não existe (conferível por `grep` dos caminhos).

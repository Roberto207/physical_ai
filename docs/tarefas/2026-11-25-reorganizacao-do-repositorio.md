# Reorganização do repositório antes da integração com LLM

**Data:** 2026-11-25

**Resposta direta:** as pastas soltas foram unificadas, os documentos desatualizados foram corrigidos e foram criados índices e uma lista de pendências. Nenhum arquivo de que a execução dependa foi movido dentro de `infra/`, `workspace/meu_ws/` ou `workspace/patrulha_oficial/`.

## Movimentos

| De | Para | Motivo |
|---|---|---|
| `workspace/exemplos/` | `workspace/llm/` | É a base da integração com LLM. O CI foi ajustado |
| `docs/rascunho/possiveis_points.md` | `workspace/mapas/pontos_mapa_lab_novo.md` | Fica ao lado do mapa; valores sem alteração |
| `docs/rascunho/numeros_de_serie` | seção "Segundo robô" de `docs/contexto/maquinas.md` | Unificação |
| `docs/relatorios/report.md` | `docs/historico/2026-11-19-relatorio-migracao.md` | Relatório datado |
| `specs/enxugamento/SPEC.md` | `docs/historico/spec-enxugamento.md` | Spec já executada |

## Arquivos novos

`docs/contexto/pendencias.md`, `specs/README.md`, `docs/historico/README.md`, `workspace/llm/README.md`.

## Correções de conteúdo

- `README.md`: tabela de entrada e árvore de pastas.
- `docs/contexto/` (máquinas, projeto, stack, ponteiros do AGENTES), `docs/decisoes/README.md` e `docs/tarefas/README.md` (três linhas que faltavam).
- Comentários de `infra/lab/rede_lab.env` (citavam Jazzy e chamavam o IP real de exemplo; os valores não mudaram), cabeçalho de `workspace/mapas/patrulha_mapa_lab_novo.yaml` (dizia estar vazio), comentário em `infra/compose/robo.yaml`.
- Aviso de documento antigo no topo de `specs/patrol-inf/kit-de-campo.md`.

## Verificação

Sem rede e sem robô: YAML e os dois Compose válidos; `bash -n`; `checar_caminhos.py` e links relativos sem erros; mapa UTILIZÁVEL e configuração APROVADA; na imagem `physical-ai:base`, `llm` 11 testes, `lab_tb4` 17, rastreio dos 35 requisitos, `flake8` limpo, os três programas abrem, `patrulha_tb4` 156 aprovados e 1 reprovado (o mesmo de antes, ver pendências).

**Não verificado:** subida de serviços, simulador, robô e o CI no GitHub.

## Efeito prático

O ponto de partida é o `README.md`; o trabalho com LLM começa em `workspace/llm/`.

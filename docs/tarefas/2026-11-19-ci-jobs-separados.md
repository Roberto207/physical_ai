# 2026-11-19: CI com jobs separados e citações quebradas removidas

**Pedido:** remover as citações a arquivos inexistentes, separar os jobs do CI e deixar claro qual erro deu.

**Resposta direta:** o job `lint` virou quatro jobs independentes, e cada nome diz o que reprovou. As citações a `docs/contexto/pendencias.md` e `docs/contexto/equipe.md` (apagados no commit `97dcfc1`) saíram dos documentos vivos. Nada de código de robô mudou.

## Por que o CI estava vermelho sem o robô ser afetado

O job `L0` (testes da lógica) passou em todos os pushes. O job `lint` reprovou por dois motivos: marcas de conflito de merge em dois `.md` (já resolvidas) e duas linhas com mais de 100 caracteres em `infra/ferramentas/checar_caminhos.py`. O ruff falhava primeiro e as etapas seguintes (`actionlint` e o checador de caminhos) nem rodavam, então um terceiro erro, as 5 citações quebradas, ficava escondido.

## O que mudou

| Job (nome que aparece no GitHub) | O que reprova | Como o erro aparece |
|---|---|---|
| Marcas de conflito de merge nos arquivos | `<<<<<<<` ou `>>>>>>>` num arquivo | Anotação `::error` com arquivo e linha |
| Estilo e erros do Python (ruff) | Linha acima de 100, import sem uso, nome indefinido | Anotação do ruff em cima da linha |
| Sintaxe do workflow do GitHub Actions (actionlint) | Erro no `ci.yml` | Saída do actionlint |
| Documentos citando arquivo que não existe | Um `.md` cita um caminho que não existe | Anotação `::error` no documento, com o caminho citado |
| L0 (humble) | Teste da lógica falhou | A etapa vermelha tem o nome do teste |

Os jobs rodam em paralelo e um não esconde o outro. O cabeçalho do `ci.yml` traz essa tabela.

Citações removidas: `README.md`, `docs/contexto/AGENTES.md`, `docs/contexto/maquinas.md`, `docs/contexto/projeto.md`, `docs/historico/resultados-jazzy.md`. Linhas longas quebradas em `checar_caminhos.py`, que também passou a emitir a anotação por citação.

## Verificação

Rodados localmente: `ruff check .` (todas as regras passam), `actionlint` no `ci.yml` (sem erros), `checar_caminhos.py` (`caminhos ok`, e uma citação falsa de teste produziu a anotação esperada) e a lógica do job de conflitos num repositório de teste. **Não verificado:** a execução no GitHub Actions, que só acontece depois do push. Citações em `docs/tarefas/`, `docs/historico/registro-de-mudancas.md` e nas specs `enxugamento` e `migracao-humble` ficaram: são registros do que valia na época, e o checador já os ignora.

## Efeito prático

Um vermelho agora aponta o tipo de erro pelo nome do job e o arquivo pela anotação. Continua sem bloquear o merge (decisão do projeto). O L0 verde continua provando só a lógica em Python, não a imagem, o Nav2 nem o robô.

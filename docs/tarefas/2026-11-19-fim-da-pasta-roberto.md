# 2026-11-19: fim da pasta Roberto/, conteúdo na raiz do repositório

**Pedido:** tirar tudo de `Roberto/`, mover para fora dela, corrigir os caminhos e subir para o git. O trabalho segue em conjunto com outras estratégias de código, mas sem essa pasta.

**Resposta direta:** todo o conteúdo de `Roberto/` agora está na raiz do repositório (`docs/`, `infra/`, `specs/`, `workspace/`, `README.md`, `ruff.toml`, `.gitignore`). A pasta `Roberto/` não existe mais. Os 109 arquivos versionados foram movidos com `git mv`-equivalente (o git os registra como renomeados, com histórico preservado), e os caminhos que citavam `Roberto/` foram corrigidos.

## O que mudou

| Onde | Antes | Depois |
|---|---|---|
| Estrutura | `Roberto/docs`, `Roberto/infra`... | `docs`, `infra`... na raiz |
| `.github/workflows/ci.yml` | filtro `paths: Roberto/**`, `working-directory: Roberto/...`, `git grep -- Roberto` | sem filtro `paths` (o CI roda em todo push/PR na `main`), `working-directory` a partir da raiz, `git grep -- .` |
| `ruff.toml`, `lab.sh`, `checar_caminhos.py` | comentários dizendo "pasta Roberto/" | "raiz do repositório" (o código não mudou: `lab.sh` e `RAIZ` usam caminho relativo, que continua valendo) |
| `docs/guias/como-rodar.md` | `~/dev/physical_ai/Roberto`, `~/physical_ai/Roberto` | `~/dev/physical_ai`, `~/physical_ai` |
| Comandos `cd ~/dev/physical_ai/Roberto/infra/docker` nos documentos de tarefa | caminho com `Roberto/` | caminho sem `Roberto/` |
| `docs/contexto/AGENTES.md`, `specs/enxugamento/SPEC.md` | `Roberto/README.md`, `Roberto/docs/tarefas/` | `README.md`, `docs/tarefas/` |

## O que ficou como estava, de propósito

- `git show jazzy-final:Roberto/<caminho>` (em `specs/migracao-humble/DESIGN.md` e `docs/tarefas/2026-11-18-f0-preparo.md`): a tag `jazzy-final` guarda a árvore antiga, em que os arquivos ainda estão sob `Roberto/`. Trocar o caminho quebraria o comando.
- Narrativa histórica de tarefas já fechadas (por exemplo, `docs/historico/registro-de-mudancas.md`): descreve o que valia na época.
- O nome "Roberto" como pessoa (decisões, autoria).
- `estudo/` (ignorado pelo git) foi movido junto no disco, e continua fora do git.

## Verificação

- Testes L0 do `patrulha_tb4` e do `lab_tb4` rodados depois da mudança (saída no fim da tarefa).
- `checar_caminhos.py` aponta 5 citações quebradas, todas para `docs/contexto/pendencias.md` e `docs/contexto/equipe.md`. Esses dois arquivos nunca estiveram no commit `HEAD`, então o problema já existia antes da mudança, e não foi tocado aqui.
- `ruff` não está instalado no notebook; o lint roda no CI.
- Não verificado: a execução do workflow no GitHub Actions (só acontece depois do push).

## Efeito prático

Os caminhos de comando agora partem de `~/dev/physical_ai`: `cd ~/dev/physical_ai/infra/docker && ./lab.sh ...`. No PC do lab, depois de `git pull`, a pasta de trabalho passa a ser `~/physical_ai` (antes, `~/physical_ai/Roberto`). Imagens e containers não dependem do caminho absoluto, mas qualquer atalho ou script local que aponte para `Roberto/` precisa ser atualizado.

# SPEC: enxugamento e organização do projeto

**Status:** Executada em 2026-11-19 (E1 a E6; relatório em `docs/tarefas/2026-11-19-enxugamento.md`). Aprovada em 2026-11-18 (portão da skill `/sdd`), com as propostas P1, P2 e P3 aprovadas
**Data:** 2026-11-18
**Rigor:** spec leve com inventário (decisão do Roberto): prosa, uma tabela arquivo → destino e critérios de pronto conferíveis por comando. Substitui a `PREVIA.md` desta pasta, que sai na etapa E6.

## 1. Objetivo

Um agente de IA ou um colega novo acha, em até 3 leituras a partir do `Roberto/README.md`, como rodar, a spec em vigor e as decisões. Nenhum arquivo versionado fica sem uso, e nenhum contradiz as regras atuais (ROS 2 Humble, o PC do laboratório simula, o notebook só roda o L0, sem analogias nas explicações).

## 2. Contexto

A migração para Humble (`specs/migracao-humble/`) já tirou os scripts e as imagens que não serviam mais. O que sobrou é texto e organização:

- **Contexto espalhado em seis lugares:**
  - `contexto/` (10 arquivos, quase todos de 16/11);
  - `docs/` (acesso ao robô, registro, tarefas, decisões);
  - a raiz (`como_rodar.md`, `caminho_estudo_humano.md`);
  - `specs/`;
  - `workspace/mapas/README.md`;
  - `progresso/`, fora do git, mas citada por 15 arquivos versionados.
- **Regras desatualizadas que os agentes leem:**
  - o `contexto/AGENTES.md` manda explicar "com uma analogia do dia a dia" (seções 5 e 6);
  - trata o limite de 7,4 GiB do notebook como regra geral (seção 4);
  - diz que o simulador leve é o principal (seção 3), o que o ADR-002 substituiu.
- **Histórico duplicado:** o `docs/registro-de-mudancas.md` (296 linhas) repete, em tabela, o que os 10 documentos de `docs/tarefas/` já contam.
- **`progresso/` (1,6 MB, fora do git):**
  - 7 textos da época do Jazzy: `testes.md`, `patrol-loop.md`, `conceitos.md`, `reuniao.md`, `origem-das-pecas.md`, `proximos-degraus.md` e `README.md`;
  - 15 pastas de evidência do L1 (1,5 MB);
  - logs de 09 e 12/11.
  - Três dos textos explicam por analogia. O único dado que não está em outro lugar são os resultados dos cenários L1 de 12 e 13/nov no Jazzy (`testes.md`, seção 6).
- **`estudo/`:** está no `.gitignore`, mas tem 28 arquivos versionados (o plano de 6 semanas, as anotações e a `.obsidian/` com tema e plugin). Entraram no git antes da regra.
- **Código sem uso:**
  - `workspace/exemplos/decisao_patrulha.py` foi superado pelo `patrulha_tb4` (o `decisao.py:8` diz "Evolução de");
  - `config/warehouse_original.yaml` era o L2, a comparação com o `patrol_loop` oficial, que ninguém roda desde que o `treino_leve.sh` saiu.

Decisões do Roberto (2026-11-18):

| Ponto | Decisão |
|---|---|
| `progresso/` | Sai. O essencial do `testes.md` vira `docs/historico/resultados-jazzy.md`. As evidências novas do L1 vão para `workspace/logs/l1/` |
| `estudo/` | Sai do git e fica no disco (`git rm --cached`) |
| Estrutura | `Roberto/README.md` como porta de entrada e um `docs/` só. A pasta `contexto/` some. `specs/` fica onde está: o `checar_rastreio.py` lê `specs/patrol-inf/DESIGN.md` pelo caminho |

## 3. Critério do que fica

Um arquivo versionado fica se atender a pelo menos um destes:

1. É executado ou testado: pelo CI, por um script de `infra/`, por um launch ou por um teste.
2. É um documento vivo citado pelo `README.md`.
3. É artefato de uma spec (`specs/*/`).
4. É registro de decisão (`docs/decisoes/`).
5. É histórico, em `docs/historico/` ou `docs/tarefas/`. O histórico não é atualizado; ganha só uma nota de que os caminhos são da época.

O que não atende a nenhum sai do repositório.

## 4. Estrutura nova

```text
Roberto/
├── README.md               porta de entrada: o que é o projeto, papel de cada máquina,
│                           "comece por aqui" e o mapa das pastas abaixo
├── docs/
│   ├── contexto/           projeto.md, equipe.md, maquinas.md, stack.md, pendencias.md, AGENTES.md
│   ├── guias/              como-rodar.md, acesso-ao-robo.md
│   ├── decisoes/           ADR-001, ADR-002 e README.md (índice dos ADRs e das decisões antigas)
│   ├── historico/          registro-de-mudancas.md (congelado), resultados-jazzy.md,
│   │                       teste-simulacao-2026-11-05.md
│   └── tarefas/            um documento por tarefa, como hoje
├── specs/                  patrol-inf/, migracao-humble/, enxugamento/ (caminho inalterado)
├── infra/                  compose/, docker/, lab/
└── workspace/              meu_ws/ (pacotes ROS), mapas/, exemplos/ (só o validar_acao), logs/ (fora do git)
```

| Pasta | Pergunta que ela responde |
|---|---|
| `docs/contexto/` | O que é o projeto, quem trabalha nele, em que máquinas, com que regras |
| `docs/guias/` | Como fazer uma coisa agora (comandos) |
| `docs/decisoes/` | Por que é assim |
| `docs/historico/` e `docs/tarefas/` | O que foi feito e quando |
| `specs/` | O que o sistema precisa fazer e como foi desenhado |

## 5. Inventário (arquivo → destino)

| Origem | Destino | Ação |
|---|---|---|
| `contexto/AGENTES.md` | `docs/contexto/AGENTES.md` | Move e reescreve. Seção 3: o simulador do ADR-002. Seção 4: o limite de 7,4 GiB vale só no notebook, que só roda o L0. Seção 5: explicação técnica, sem analogia (o que vale no CLAUDE.md do Roberto). Seção 6: caminhos novos e a regra do registro (ver a seção 6 desta spec). Seção 7: a tabela "onde achar" nova |
| `contexto/projeto/briefing-original.md`, `escopo.md`, `missoes-iniciais.md` | `docs/contexto/projeto.md` | Funde em seções (briefing citado sem mudança, escopo, missões) |
| `contexto/projeto/decisoes.md` | `docs/decisoes/README.md` | Move. Vira o índice: os ADRs no topo e a tabela das decisões antigas embaixo |
| `contexto/equipe/roberto.md` | `docs/contexto/equipe.md` | Move |
| `contexto/infra/maquina-roberto.md` | `docs/contexto/maquinas.md` | Funde com os fatos do PC do laboratório e do robô. Hoje eles estão em `specs/patrol-inf/kit-de-campo.md` e em `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md`: Humble, Discovery Server id 1, domínio 0, `/robot1`, rotas e o papel de cada máquina. Os dois documentos de origem não mudam e passam a apontar para cá |
| `contexto/infra/teste-simulacao-2026-11-05.md` | `docs/historico/teste-simulacao-2026-11-05.md` | Move |
| `contexto/tecnologias/fontes-e-stack.md` | `docs/contexto/stack.md` | Move e atualiza a stack para Humble (Fortress, `lab_tb4`, loopback vendorizado) |
| `contexto/pendencias.md` | `docs/contexto/pendencias.md` | Move e limpa: fica só o que está aberto. Os itens fechados vão para o fim de `docs/historico/resultados-jazzy.md` |
| `como_rodar.md` | `docs/guias/como-rodar.md` | Move |
| `docs/acesso-ao-robo-por-cabo.md` | `docs/guias/acesso-ao-robo.md` | Move |
| `docs/registro-de-mudancas.md` | `docs/historico/registro-de-mudancas.md` | Move e congela |
| `docs/decisoes/ADR-001…`, `ADR-002…` | Ficam | Sem mudança |
| `docs/tarefas/*.md` | Ficam | Uma nota no topo de cada: "caminhos anteriores ao enxugamento; o mapa está no `README.md`" |
| `progresso/testes.md` (+ o essencial do `patrol-loop.md` e do `proximos-degraus.md`) | `docs/historico/resultados-jazzy.md` | Resumo técnico: os cenários L1 aprovados em 12 e 13/nov (nome, tempo, veredito), as falhas vistas e onde cada uma foi resolvida, e o que o `patrol_loop` oficial mostrou. Os próximos degraus que ainda valem vão para as pendências |
| `progresso/` (o resto) | — | Apagado depois do resumo, **com o ok do Roberto no momento**: está fora do git, então é irreversível |
| `estudo/` (28 arquivos versionados) | Disco local | `git rm -r --cached estudo` |
| `caminho_estudo_humano.md` | `estudo/` (local) | Move para dentro de `estudo/` e sai do git junto |
| `workspace/exemplos/decisao_patrulha.py`, `test_decisao_patrulha.py` | — | Saem. O `decisao.py:8` passa a dizer "evolução do exemplo `workspace/exemplos/decisao_patrulha.py` (tag `jazzy-final`)" |
| `workspace/exemplos/validar_acao.py`, `test_validar_acao.py` | Ficam | São a camada de segurança da missão do LLM, até a spec dela |
| `workspace/mapas/README.md` | Fica | Tira a menção ao `progresso/` |
| `patrulha_tb4/config/warehouse_original.yaml` | — | **Proposta (seção 6):** sai |
| `infra/docker/teste_l1.sh` | Fica | As evidências vão para `workspace/logs/l1/<data>-<cenario>/` |
| `.gitignore` | Fica | Sai a linha `progresso/`. Ficam `estudo/` e `workspace/logs/` |
| `specs/enxugamento/PREVIA.md` | — | Sai na E6 (esta spec a substitui) |
| `specs/patrol-inf/*`, `specs/migracao-humble/*` | Ficam | Só as citações de caminhos mudam, nas linhas que apontam para `contexto/`, `progresso/` ou `como_rodar.md` |

## 6. Propostas (as três aprovadas no portão de 2026-11-18)

| # | Proposta | Por quê | Efeito |
|---|---|---|---|
| P1 | O `registro-de-mudancas.md` congela. Daqui em diante, o registro é uma tabela "data, tarefa, documento" no `docs/tarefas/README.md`, uma linha por tarefa. A regra do AGENTES (seção 6) e a memória `doc-por-tarefa` mudam junto | Hoje toda mudança é escrita duas vezes: no documento da tarefa e na tabela do registro | O que mudou fica em um lugar; o índice só aponta |
| P2 | `config/warehouse_original.yaml` sai, e o teste parametrizado `test_as_configuracoes_do_pacote_carregam` perde esse caso (o CFG-05 da `migracao-humble` permite mexer no `test_config.py`) | O L2 era a comparação com o `patrol_loop` oficial. Ninguém mais roda esse oficial | Uma configuração a menos para manter |
| P3 | Um checador de caminhos, `infra/ferramentas/checar_caminhos.py` (Python puro), no job `lint` do CI. Ele lê os `.md` vivos (fora de `docs/historico/` e `docs/tarefas/`), extrai os caminhos entre crases que começam com uma pasta do repositório e falha se algum não existir | É a classe do problema que esta spec corrige à mão: documento que aponta para arquivo que não existe (o `rede-lab-explicada.md` da F0 foi um caso) | O próximo arquivo movido sem corrigir as citações deixa o CI vermelho |

## 7. Critérios de pronto

| # | Critério | Como conferir |
|---|---|---|
| C1 | Nenhum documento vivo cita caminho antigo | `git grep -nE '(^|[^a-z/])contexto/|progresso/|como_rodar\.md|estudo/' -- . ':!docs/historico' ':!docs/tarefas' ':!specs/enxugamento'` vazio |
| C2 | `estudo/` fora do git e no disco | `git ls-files estudo` vazio e `ls estudo/plano` lista os arquivos |
| C3 | A pasta `contexto/` não existe mais | `test ! -e contexto` |
| C4 | O AGENTES não pede analogia | `grep -niE 'analogia|dia a dia' docs/contexto/AGENTES.md` só em frase que proíbe |
| C5 | O README leva a tudo | O `README.md` tem link para `docs/guias/como-rodar.md`, para `specs/` e para `docs/decisoes/README.md` |
| C6 | Nada de comportamento mudou | L0 (`patrulha_tb4`, `lab_tb4`, `exemplos`), rastreio, ruff, actionlint e `docker compose config` iguais aos de antes da E1 |
| C7 | As evidências do L1 vão para o lugar novo | `grep -n 'workspace/logs/l1' infra/docker/teste_l1.sh` |
| C8 | Se a P3 for aprovada, o checador passa | `python3 infra/ferramentas/checar_caminhos.py` com saída 0 |

## 8. O que NÃO muda

Nenhum código do robô, launch, compose, imagem ou script de `infra/`, exceto o caminho das evidências no `teste_l1.sh`. Nenhum requisito das specs. O caminho de `specs/`. O conteúdo dos documentos históricos, que só ganham a nota de topo.

## 9. Ordem de execução (depois do portão)

| Etapa | O quê | Commit |
|---|---|---|
| E1 | Escrever o `docs/historico/resultados-jazzy.md` a partir do `progresso/` | `docs: resumo dos resultados Jazzy` |
| E2 | Mover e fundir para `docs/` (`git mv` onde for move, para manter o histórico do git) | `docs: estrutura única em docs/` |
| E3 | Escrever o `README.md`; reescrever o `AGENTES.md`; P1, se aprovada | `docs: README e AGENTES` |
| E4 | Código: `exemplos/`, P2 e o `teste_l1.sh` | `chore: código sem uso` |
| E5 | `estudo/` fora do git; o `progresso/` apagado **com o ok do Roberto** | `chore: estudo fora do git` |
| E6 | Citações, P3, a `PREVIA.md` sai, documento da tarefa, verificação C1 a C8 | `docs: citações e verificação` |

Sem push: os commits ficam locais até o Roberto publicar.

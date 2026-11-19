# Relatório: migração para ROS 2 Humble e enxugamento do projeto

**Data:** 2026-11-19
**Base verificada:** commit `5defde9` na `main`. Na cópia local, `origin/main` aponta para o mesmo commit, então não há commit local pendente de envio.
**Escopo:** as duas frentes fechadas em 2026-11-18 e 2026-11-19: a migração das imagens e da infraestrutura para Humble (`specs/migracao-humble/`) e o enxugamento e a reorganização de `docs/` (`specs/enxugamento/SPEC.md`).

## 1. Resposta direta

**Migração para Humble:** o código das fases F0 a F4 está pronto e commitado. A parte que roda sem Docker e sem robô passa: 133 testes em `patrulha_tb4`, 17 em `lab_tb4` e 11 em `workspace/exemplos`. O que depende do PC do laboratório ou do robô físico não foi executado: o build das imagens Humble (V1), o teste de fumaça do Gazebo, os 11 cenários do L1, a SEG-01 com a imagem antiga e a V5 no robô. Nada disso tem registro de execução no repositório. O robô não foi tocado.

**Enxugamento:** as etapas E1 a E6 estão feitas. O `contexto/` virou `docs/contexto/`, o `progresso/` foi apagado, o `estudo/` saiu do git, três arquivos de código sem uso saíram e o checador de caminhos foi criado.

**Um defeito grave:** o commit `97dcfc1` ("chore: Limpeza") apagou os arquivos `pendencias.md` e `equipe.md`, que ficavam em `docs/contexto/`. Essas citações continuam nos documentos vivos `README.md`, `docs/contexto/AGENTES.md` e `docs/contexto/maquinas.md`. Por isso o checador de caminhos (`infra/ferramentas/checar_caminhos.py`) sai com 1 e lista 5 citações quebradas. O job `lint` do CI deve estar vermelho desde o último push. A lista de pendências do projeto deixou de existir na árvore atual. O conteúdo continua no histórico (seção 6, item 1).

## 2. Linha do tempo

| Data | Commit | O que foi feito |
|---|---|---|
| 2026-11-16 | `c139fdd` a `bc354ad` | Modo SLAM, compose e alvos, rede do robô real. Ainda em Jazzy |
| 2026-11-18 | `d5d7716` | Spec da migração (DEFINE e DESIGN) |
| 2026-11-18 | `7cf58bb` | F0: preparo. Tag `jazzy-final` criada, conflitos de merge resolvidos |
| 2026-11-18 | `41cf461` | F1: imagens Humble, guarda de distro, modo robô |
| 2026-11-18 | `037a73d` | F2: pacote `lab_tb4` e Gazebo Fortress |
| 2026-11-18 | `7198912` | F3: L1 leve com o loopback vendorizado |
| 2026-11-18 | `5e31a25` | F4: limpeza, CI só com Humble, documentação |
| 2026-11-19 | `d35388c` | E1: resumo dos resultados Jazzy |
| 2026-11-19 | `5e70940` | E2: estrutura única em `docs/` |
| 2026-11-19 | `f4bf4f6` | E3: `README.md` novo, `AGENTES.md` reescrito, registro por tarefa |
| 2026-11-19 | `da467c5` | E4: código sem uso removido |
| 2026-11-19 | `72fd188`, `10b628c` | E5: `estudo/` fora do git, `progresso/` apagado |
| 2026-11-19 | `9f3e422` | E6: citações corrigidas, checador de caminhos no CI, documento da tarefa |
| 2026-11-19 | `97dcfc1` | "chore: Limpeza". Apagou `pendencias.md` e `equipe.md`. Não estava na spec |
| 2026-11-19 | `7b64115`, `4cbdcb7`, `9dd4a4c`, `41185b8` | Mapa do laboratório, registro, correção no script do SLAM e merge do PR #2 (de outro colaborador) |
| 2026-11-19 | `5defde9` | `Roberto/` removida: o conteúdo foi para a raiz e os caminhos foram corrigidos |

## 3. Migração para Humble

### 3.1 O que foi decidido

| Decisão | Registro | Consequência |
|---|---|---|
| Todas as imagens vão para Humble | `docs/decisoes/ADR-001-ros2-humble.md` | O robô do laboratório roda Humble (Ubuntu 22.04, Python 3.10). Nós Jazzy na rede dele derrubaram o serviço `turtlebot4` em 2026-11-16 |
| O Gazebo Fortress sem janela no PC do lab é o simulador principal | `docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md` | O L1 leve (loopback vendorizado) vira o nível de injeção de falhas, com os 11 cenários |
| O Jazzy fica guardado | Tag git `jazzy-final` e imagens `physical-ai:jazzy-<alvo>` (PRE-02) | Voltar ao Jazzy é um `git checkout` mais um `docker tag` |
| Launches de ambiente saem do `patrulha_tb4` | Pacote novo `lab_tb4` (F2) | O `patrulha_tb4` sobe só o próprio nó. Os launches são `launch.py`, sem shell compondo nós ROS |

### 3.2 O que entrou no código

| Fase | Commit | Conteúdo |
|---|---|---|
| F0 | `7cf58bb` | Tag `jazzy-final`, conflitos de merge resolvidos |
| F1 | `41cf461` | `Dockerfile` com `FROM ros:humble-ros-base` nos estágios; `construir_imagem.sh` com a conferência de memória (IMG-06) e a tag `jazzy-<alvo>` (PRE-02); `lab.sh robo` com a guarda SEG-01 |
| F2 | `037a73d` | `lab_tb4` (launches `gazebo`, `sim_leve` e `l1`, base falsa, vigia, conferidor de cenários); `sim.yaml` e `robo.yaml` com os mesmos nomes de serviço (SIM-02) |
| F3 | `7198912` | Loopback vendorizado em `workspace/meu_ws/src/terceiros/nav2_loopback_sim/` com `LICENSE` e `ORIGEM.md`; `teste_l1.sh` com os cenários em `lab_tb4/config/cenarios_l1.yaml` |
| F4 | `5e31a25` | Remoção de `ros.sh`, `treino_leve.sh`, `run_sim_headless.sh` e `sim_headless.launch.py`; a pasta de ferramentas antiga removida; CI com matriz só `humble`; `como_rodar.md`, kit de campo e adendo no DESIGN da `patrol-inf` atualizados |

### 3.3 Estado das verificações da spec

A spec (`specs/migracao-humble/DEFINE.md`) define os requisitos. Esta tabela separa o que foi conferido por leitura ou execução no notebook do que depende do PC do laboratório.

| Verificação | Estado | Como foi ou será conferido |
|---|---|---|
| L0: testes de `patrulha_tb4`, `lab_tb4` e `exemplos` | Passa (133, 17 e 11) | `python3 -m pytest -q` em cada pacote, rodado nesta geração |
| IMG-01: `FROM` só `ros:humble-ros-base` ou estágio interno | Passa | `grep '^FROM' infra/docker/Dockerfile`: quatro linhas, todas Humble ou estágio interno |
| CI-01: matriz `l0` só `humble` | Passa | `.github/workflows/ci.yml` |
| PRE-01: tag `jazzy-final` | Passa | `git tag -l` lista `jazzy-final` |
| G1 a G5 e IMG-05 (conferidos na F4) | Passa, na época | Conferidos no notebook em 2026-11-18 (`docs/tarefas/2026-11-18-f4-limpeza.md`, seção 3). Não reconferidos aqui |
| Lint (`ruff`) e `actionlint` | Não verificado no notebook | Não estão instalados. Rodam no CI |
| `docker compose config` (sim e robo) | Não reexecutado nesta geração | Último resultado: válido, em 2026-11-19 (`docs/tarefas/2026-11-19-enxugamento.md`, seção 4) |
| V1: build das imagens Humble no PC do lab | Pendente | `infra/docker/construir_imagem.sh base robo sim`, no PC do lab |
| SEG-01 com a imagem Jazzy | Pendente | Checklist da F4, item 3 |
| SIM-01: fumaça do Gazebo (`/scan`, `/odom`, `/tf`, `/dock_status`) | Pendente | Checklist da F4, item 4 |
| SIM-04 e SIM-05: 11 cenários L1 com veredito | Pendente | Checklist da F4, item 6 |
| V5: robô real | Pendente, só com permissão do Roberto no dia | Checklist da F4, item 7 |
| M-GZH: medição no PC | Fora de escopo | Só com pedido explícito do Roberto (ADR-002) |

### 3.4 Divergência conhecida

O DOC-04 da spec pede uma entrada em `docs/historico/registro-de-mudancas.md` para cada fase. A P1 da spec do enxugamento congelou esse arquivo e trocou por uma tabela em `docs/tarefas/README.md`. O DEFINE ainda diz o contrário. A decisão posterior vale, mas o DEFINE deveria ser corrigido para evitar que alguém siga a regra antiga.

## 4. Enxugamento

### 4.1 O que saiu

| Item | Destino | Por quê |
|---|---|---|
| `progresso/` (1,6 MB, fora do git) | Apagado. O resumo ficou em `docs/historico/resultados-jazzy.md` | Textos da época do Jazzy, muitos explicando por analogia, e evidências duplicadas. Apagado com o ok do Roberto. Irreversível |
| `estudo/` (28 arquivos versionados) | Fora do git, continua no disco | O material de estudo é pessoal. Está no `.gitignore` |
| `contexto/` | Virou `docs/contexto/` (AGENTES, projeto, maquinas, stack) | Eram seis lugares com contexto. Agora é um `docs/` só |
| `docs/historico/registro-de-mudancas.md` | Congelado em `docs/historico/` | Repetia o que cada documento de tarefa já dizia |
| `decisao_patrulha.py` (em `workspace/exemplos/`) e o teste dele | Apagados (8 testes do exemplo) | Superado pelo `patrulha_tb4`. O `decisao.py` cita a versão antiga pela tag `jazzy-final` |
| `config/warehouse_original.yaml` | Apagado (1 caso parametrizado de configuração) | Era o L2, a comparação com o `patrol_loop` oficial, que ninguém roda mais |
| PREVIA.md da pasta de enxugamento | Apagado | A `SPEC.md` substitui |
| `Roberto/` | Conteúdo na raiz do repositório | Pedido do Roberto. `git` registra como renomeação, com histórico preservado |

### 4.2 Contagem de testes antes e depois

| Pacote | Antes da E4 | Depois (E6, e nesta geração) | Motivo da diferença |
|---|---|---|---|
| `patrulha_tb4` | 134 | 133 | Sai o caso `warehouse_original.yaml` |
| `lab_tb4` | 17 | 17 | Sem mudança |
| `workspace/exemplos` | 19 | 11 | Saem os 8 testes do `decisao_patrulha.py` |

### 4.3 Critérios de pronto da SPEC

| # | Critério | Estado agora | Observação |
|---|---|---|---|
| C1 | Nenhum documento vivo cita caminho antigo | Passa | O `grep` retorna só o próprio checador e o `.gitignore` |
| C2 | `estudo/` fora do git | Passa | `git ls-files estudo` retorna 0 |
| C3 | `contexto/` não existe | Passa | |
| C4 | AGENTES não pede analogia | Passa | Só a frase que proíbe aparece |
| C5 | README leva a tudo | Passa | |
| C6 | Nada de comportamento mudou | Passa, em parte | Testes L0 conferidos. `ruff` e `actionlint` não rodam no notebook |
| C7 | Evidências do L1 em `workspace/logs/l1/` | Passa | |
| C8 | Checador passa | Reprovado | 5 citações quebradas, por causa do item 1 da seção 6 |

### 4.4 Checador de caminhos (P3)

`infra/ferramentas/checar_caminhos.py` lê os `.md` vivos, extrai os trechos entre crases que começam com `docs/`, `infra/`, `specs/` ou `workspace/` e falha se algum não existir. Ele exclui `docs/historico/`, `docs/tarefas/`, `specs/enxugamento/`, `specs/migracao-humble/` e `estudo/`. Esse checador está no job `lint` do CI. Este relatório não cita caminho que não exista entre crases, para não aumentar a lista de citações quebradas.

## 5. Verificações feitas nesta geração

| Verificação | Comando | Resultado |
|---|---|---|
| Testes L0 | `python3 -m pytest -q` em `patrulha_tb4`, `lab_tb4` e `workspace/exemplos` | 133, 17 e 11, todos passam |
| Checador de caminhos | `python3 infra/ferramentas/checar_caminhos.py` | Saída 1, 5 citações quebradas |
| Estudo fora do git | `git ls-files estudo \| wc -l` | 0 |
| Tag Jazzy | `git tag -l` | `jazzy-final` |
| Base da migração | `git rev-list --count jazzy-final..main` | 17 commits depois da tag |
| Dockerfile | `grep '^FROM' infra/docker/Dockerfile` | Só `ros:humble-ros-base` e estágios internos |
| Sincronia com o remoto | `git rev-list --count origin/main..main` | 0 (o remoto não foi consultado pela rede) |

## 6. Problemas encontrados, do mais grave ao menos

1. **Pendências e equipe apagadas (commit `97dcfc1`).** Os arquivos `pendencias.md` e `equipe.md` estavam em `docs/contexto/` desde `5e70940` e saíram em `97dcfc1`, sem explicação no commit. A lista de pendências tinha o que estava aberto: a data de entrega, o provedor de LLM, a medição M-GZ, a falha do Nav2 no leve, o status do robô no Wi-Fi e o checklist da migração. O conteúdo está recuperável com `git show 97dcfc1^:Roberto/docs/contexto/pendencias.md` e `git show 97dcfc1^:Roberto/docs/contexto/equipe.md`. O relatório da tarefa `docs/tarefas/2026-11-19-fim-da-pasta-roberto.md` diz que esses arquivos "nunca estiveram no commit HEAD". Isso está errado: estiveram, e saíram num commit anterior ao HEAD. **Ação recomendada:** restaurar os dois arquivos, atualizar a seção de Humble em `pendencias.md` e rodar o checador de novo.

2. **Divergência de push.** Os documentos da F4 e do enxugamento dizem "sem push". Pela cópia local, `origin/main` está em `5defde9`, então o envio provavelmente já aconteceu. Não consultei o GitHub, então isso não está confirmado. Se o envio aconteceu, o job `lint` do CI rodou com o item 1 quebrado.

3. **Memória desatualizada.** A nota de memória `migracao-humble` ainda manda seguir `Roberto/specs/...` e cita a `PREVIA.md`, que não existe mais. Não foi alterada nesta geração.

4. **DOC-04 do DEFINE.** Ver a seção 3.4.

5. **Verificações sem registro.** O `ruff`, o `actionlint` e o `docker compose config` não foram reexecutados nesta geração. O último resultado conhecido está nos documentos de tarefa.

## 7. O que falta

### 7.1 Migração (no PC do lab, na ordem)

1. `git pull` (o código já está no remoto, ver item 2 da seção 6).
2. V1: `infra/docker/construir_imagem.sh base robo sim`. Esperado: tags `jazzy-<alvo>` criadas e `ROS_DISTRO da imagem nova: humble`.
3. SEG-01 sem robô: `lab.sh robo estado` deve responder `RECUSADO (SEG-01)`.
4. Fumaça do Gazebo: `lab.sh sim subir gazebo`, depois `/scan`, `/odom`, `/tf` e `/dock_status` com `ros2 topic echo --once`.
5. Mapa no Gazebo: `subir gazebo slam rviz`, `undock`, `teleop`, `salvar`.
6. Os 11 cenários L1 com `teste_l1.sh`, todos com `APROVADO`.
7. V5 no robô real: só com permissão do Roberto no dia. Antes, a documentação oficial (Discovery Server e Generating a map, aba Humble). Depois, `lab.sh robo checar-rede` com `REDE OK` e 5 minutos de `journalctl` sem `Bad alloc` nem `oom-kill`.

Até a V5 passar, o aviso "não use o `lab.sh robo`" continua valendo.

### 7.2 Pendências de projeto (recuperadas do commit `97dcfc1^`)

Os itens de maior peso, na ordem em que estavam no arquivo:

- Qual é a data exata de entrega, e "pronto" é em simulação ou no robô real.
- Qual provedor de LLM usar (a OpenAI exige chave paga) e se o INF tem GPU ou créditos.
- Medição M-GZ no Gazebo: só com pedido do Roberto.
- Falha do Nav2 ao subir no leve ("transform from base_link to odom did not become available"), vista em 2 de 16 subidas. Causa não confirmada.
- `/battery_state` do Gazebo sem mensagens nos testes. Causa provável: o tempo simulado é mais lento que o real.
- Robô no Wi-Fi `PixelLab-2.4GHz`: confirmar a reconexão e pedir reserva de DHCP ao INF.
- Modelo do robô: o log diz OAK-D-PRO, o que indica o modelo padrão, não o Lite. Confirmar com o INF.

## 8. Decisões que tomei nesta geração

- O relatório fica em `docs/relatorios/report.md`. Criei a pasta `docs/relatorios/` para ele. Se preferir na raiz ou em `docs/tarefas/`, é só mover.
- Não alterei código, documentos de tarefa nem o histórico do git. Não restaurei `pendencias.md` nem `equipe.md`. A restauração muda o repositório e precisa do seu ok.
- Não criei entrada na tabela de `docs/tarefas/README.md`, porque um relatório não é uma tarefa.

## 9. Efeito prático

Para o trabalho do Roberto, o repositório está pronto para o PC do laboratório executar a V1, mas o robô segue bloqueado até a V5. Antes da próxima sessão, convém restaurar as pendências, porque o checklist de migração e a lista de dúvidas para o coordenador estão só no histórico. Para a banca, a parte da migração que pode ser mostrada hoje é a de testes sem Docker e a documentação das decisões. O build no PC e o robô ainda não têm registro de execução.

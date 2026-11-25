# Guias das duas patrulhas e cola de comandos

**Data:** 2026-11-25

**Resposta direta:** foram criados três guias em `docs/guias/`, com comandos comentados para copiar e colar.

| Arquivo | Para que serve |
|---|---|
| `docs/guias/patrulha-volta-a-doca.md` | Subir os serviços, rodar `patrol_loop2.py` (ida e volta, termina na doca) e derrubar tudo; cita a variante `rodar.sh` |
| `docs/guias/patrulha-loop-continuo.md` | O mesmo para `loop.py` (loop contínuo), com parada, volta à doca e encerramento |
| `docs/guias/comandos-basicos.md` | Rede, subir, logs, descer, sensores, RViz, mapa, simulador, imagens e testes |

## Como foi verificado

- Os comandos foram montados a partir de `infra/docker/lab.sh`, `infra/compose/robo.yaml`, dos três programas em `workspace/patrulha_oficial/upstream/` e de `docs/guias/acesso-ao-robo.md`.
- Executados em 25/11, só leitura: `checar-rede` (REDE OK), leitura de `dock_status` e de `battery_state`, e frequência de `scan` (cerca de 8 Hz) e `odom` (cerca de 20 Hz).
- `python3 infra/ferramentas/checar_caminhos.py` para os caminhos citados.

## O que não foi verificado

- Nenhum comando de movimento foi executado nesta tarefa. Não há registro nesta pasta de ensaio físico do `loop.py` nem do `patrol_loop2.py`.
- Não foi testado se o `Ctrl+C` encerra o contêiner aberto por `compose run -T`; por isso os guias mandam conferir com `docker ps`.
- Não foram executados nesta tarefa: subida dos serviços, comandos de SSH, de mapa, do simulador e de construção de imagens.

## Pendência

`patrol_loop.py` e `loop.py` usam os pontos 1 e 4 antigos, enquanto `workspace/patrulha_oficial/README.md` diz que foram medidos de novo em 23/11. Confirmar qual vale.

## Efeito prático

Cada atividade tem uma sequência única, do `checar-rede` ao `parar`.

## Segunda etapa: unificação dos documentos

**Resposta direta:** os dois guias antigos da `patrulha_tb4` (`como_rodar_patrol_loop.md` e `patrulha_mapa_lab_novo.md`) foram removidos, e o que continua válido neles entrou em `docs/guias/como-rodar.md`, que virou o índice. Recuperação: `git show e76c749:docs/guias/<nome>`.

| Arquivo | Mudança |
|---|---|
| `docs/guias/como-rodar.md` | Reescrito: índice, situação atual, testes, imagens, simulador, mapa, `patrulha_tb4` |
| `workspace/patrulha_oficial/README.md` | Reescrito conforme o código atual, inclusive os pontos 1 e 4 |
| `README.md`, `workspace/mapas/README.md`, `docs/contexto/maquinas.md` | Ponteiros e fatos atualizados |
| `docs/guias/acesso-ao-robo.md`, `infra/docker/lab.sh`, `infra/lab/rede_lab.env` | Caminhos antigos corrigidos (só texto) |

Nenhum código de patrulha foi apagado ou movido. O formato da configuração da `patrulha_tb4` não foi copiado: o modelo é `workspace/meu_ws/src/patrulha_tb4/config/inf_lab.yaml`.

**Não alterado, depende do Roberto:** a regra da V5 em `docs/contexto/AGENTES.md` e `docs/contexto/maquinas.md`; os avisos equivalentes em `infra/compose/robo.yaml` e `specs/`; comentários que citam Jazzy em `infra/lab/rede_lab.env`.

## Terceira etapa: programas movidos, mapas antigos apagados

**Resposta direta (decisões do Roberto em 25/11):** a regra da V5 foi retirada; os pontos são os de `docs/rascunho/possiveis_points.md`, sem os graus; os programas saíram de `upstream/`; ficou só o mapa `mapa_lab_novo`.

| Mudança | Arquivos |
|---|---|
| Programas um nível acima | `workspace/patrulha_oficial/` (`patrol_loop.py`, `patrol_loop2.py`, `loop.py`), `rodar.sh`, guias e README |
| `loop.py` importa pontos e limites do `patrol_loop.py` | Um só lugar para mudar um ponto |
| Opção desconhecida passa a ser erro nos três programas | Antes era ignorada, e a patrulha começava |
| Mapa padrão da `localizacao` | `infra/compose/robo.yaml`: de `/mapas/lab.yaml` (inexistente) para `/mapas/mapa_lab_novo.yaml` |
| Apagados | `lab_teste.*`, `teste_maze.*`, `inf_lab_preenchido.yaml` (usava o `lab_teste`), `patrulha_teste_pontos_1_2.yaml`. Recuperar: `git show e76c749:workspace/mapas/<arquivo>` |
| Mantido | `patrulha_mapa_lab_novo.yaml`: configuração da `patrulha_tb4` para o mapa atual |
| Aviso da V5 retirado | `docs/contexto/AGENTES.md`, `docs/contexto/maquinas.md`, `docs/guias/como-rodar.md`, `infra/compose/robo.yaml`, `specs/patrol-inf/kit-de-campo.md`. As demais regras de segurança continuam |

`docs/relatorios/report.md`, `docs/tarefas/`, `docs/historico/` e as specs de design descrevem o que valia na data e não foram reescritos.

### Verificação da terceira etapa

Na imagem `physical-ai:base`, com a rede desligada (nenhum acesso ao robô):

- Os três programas abrem (`--help`), recusam opção desconhecida com código 2 e, sem robô, encerram com "Robô não confirmado na doca" (ou, no `--voltar-doca`, sem confirmar a doca).
- `loop.py` recebe do `patrol_loop.py` os mesmos pontos de `docs/rascunho/possiveis_points.md`.
- `flake8` (regras E e F, linha de 100) sem erros.
- Testes: `patrulha_tb4` com 156 aprovados e 1 reprovado (`test_o_modulo_de_validacao_nao_importa_ros`), que passa quando roda sozinho; o código desse pacote não foi alterado. `lab_tb4` com 17 e `workspace/exemplos` com 11 aprovados.
- No host: `robo.yaml` válido, `lab.sh conferir` do mapa UTILIZÁVEL, configuração restante APROVADA e `checar_caminhos.py` sem erros.

**Não verificado:** nenhum serviço foi subido e o robô não se moveu. Os programas alterados ainda não rodaram no robô.

# Tarefa: pedido de retorno à doca sob demanda (PAT-23)

**Data:** 2026-11-19
**Pedido:** poder mandar o robô voltar à doca durante a patrulha, sem esperar uma condição de bateria. Entre as opções estudadas, o Roberto escolheu a B: o nó da patrulha oferece um serviço, e a decisão reaproveita o caminho que já existia para a bateria baixa.
**Spec:** `specs/patrol-inf/DEFINE.md` (PAT-23, PAT-23b, PAT-23c, PAT-23d e PAT-23e) e `specs/patrol-inf/DESIGN.md`.
**Situação:** código e testes L0 prontos e conferidos no notebook. **Não rodou no Gazebo nem no robô.** O que não foi verificado está na seção 4.

## 1. Resposta direta

A patrulha ganhou o serviço `patrulha/voltar_doca` (tipo `std_srvs/srv/Trigger`). Quando alguém o chama, a máquina de estados cancela o destino em andamento, leva o robô à aproximação da doca, faz o dock (com as mesmas confirmações e tentativas de sempre) e **encerra com o código 0**, sem carregar a bateria nem retomar a ronda. O Ctrl+C continua como antes: para onde o robô estiver, sem ir à doca.

## 2. O que mudou, arquivo por arquivo

| Arquivo | Mudança | Requisito |
|---|---|---|
| `specs/patrol-inf/DEFINE.md` | PAT-23 a PAT-23e, o termo "Pedido de retorno à doca", o PAT-23 na lista de cancelamentos que não contam como destino falho, o código 0 também para o retorno por comando | PAT-23 a PAT-23e |
| `specs/patrol-inf/DESIGN.md` | Evento `doca_pedida` na lista fechada, descrição do serviço no `no_patrulha.py` e linhas na tabela Requisito → teste | OBS-01 |
| `workspace/meu_ws/src/patrulha_tb4/patrulha_tb4/decisao.py` | `POR_COMANDO`, campo `Entrada.pedido_doca` e as reações por fase (ver a seção 3) | PAT-23 a PAT-23d |
| `.../patrulha_tb4/registro.py` | `doca_pedida` na tupla `EVENTOS` | OBS-01 |
| `.../patrulha_tb4/no_patrulha.py` | O `Monitor` cria o serviço; o `Patrulha` guarda um `threading.Event` e o passa à decisão como `pedido_doca` | PAT-23e |
| `.../patrulha_tb4/package.xml` | Dependência de execução `std_srvs` | PAT-23e |
| `.../test/conftest.py`, `test_decisao.py`, `test_registro.py` | `Mundo` aceita `pedido_doca_em`; 22 testes novos; o teste de eventos vistos inclui o novo cenário | TST-02 |
| `infra/docker/lab.sh` | Ação nova `voltar-doca`: no `robo`, pede `SIM`; chama `ros2 service call <ns>/patrulha/voltar_doca` num container `ferramentas`, com `timeout` de 30 s; não envia dock nem undock (SEG-06) | PAT-23e |
| `docs/guias/como-rodar.md` | Reorganizado: seção 5 (patrulha no `sim`) e seção 7 (patrulha no `robo`), cada uma com pré-requisitos, passo a passo, `voltar-doca`, como parar e os códigos de saída. As seções 3 e 6 ficam só com o mapa. Os comandos para rodar a patrulha normal não mudaram | |

Não mudaram: `config.py`, `pontos.py`, o launch, o `lab_tb4`, os compose e os 11 cenários L1. No `lab.sh`, só entrou a ação nova; nenhuma ação existente mudou.

## 3. Como a decisão trata o pedido

O pedido é um **nível**: o `Event` do nó liga quando o serviço é chamado e nunca desliga. A `decidir()` é idempotente, então chamar o serviço duas vezes não grava dois `doca_pedida`: ou a fase muda, ou o motivo já é `comando`, ou o sistema já está encerrando.

| Fase no momento do pedido | O que acontece |
|---|---|
| `patrulhando` | Grava `doca_pedida`, cancela o destino (não conta como falho), envia a aproximação da doca com o motivo `comando` |
| `saindo_doca` | O pedido fica pendente. Com o undock bem-sucedido, vale como em `patrulhando`, no mesmo ciclo. Com o undock falho, vale o PAT-16 (código 5) |
| `indo_doca`, `encaixando` (por bateria) | Mantém a ação, grava `doca_pedida` e troca o motivo para `comando`; com o dock confirmado, encerra com 0 em vez de carregar |
| `indo_doca`, `encaixando` (por falhas seguidas) | Nenhuma mudança: encerra com 7 (PAT-08) |
| `iniciando`, `carregando`, com `is_docked: true` | Grava `doca_pedida` e `encerrado`, sem enviar ação, e sai com 0 |
| `iniciando`, `carregando`, sem `is_docked: true` | Fica pendente; valem o PAT-17 e o ramo de reencaixe do `carregando` |
| `encerrando` | Ignorado |

Ordem de precedência no mesmo ciclo: o resultado de um destino que terminou é tratado primeiro (um destino falho conta); depois vem o pedido, que prevalece sobre bateria baixa, crítica, perdida e falhas seguidas; o sinal (PAT-15) prevalece sobre o pedido. Se o dock falhar em todas as tentativas, vale o PAT-11 (código 4).

O crítico EARS (`sdd-ears-critico`) apontou ambiguidades na primeira redação do DEFINE: a precedência entre o pedido e a bateria, o que fica pendente, o prazo de 2 s do PAT-23c e a mistura de três coisas no PAT-23e. A redação atual corrige esses pontos.

## 4. Verificação

| Verificação | Resultado |
|---|---|
| Testes L0 do `patrulha_tb4` | 155 passam (eram 133; 22 novos) |
| Rastreio TST-02 | 35 requisitos L0 com teste (eram 31; entram PAT-23, PAT-23b, PAT-23c e PAT-23d) |
| `lab_tb4` e `workspace/exemplos` | 17 e 11 passam, sem mudança |
| Lista de eventos do DESIGN igual à tupla `EVENTOS` | Passa (`test_a_lista_de_eventos_e_a_do_design`) |
| `py_compile` de `decisao.py`, `registro.py` e `no_patrulha.py`; `bash -n` no `lab.sh` | Passa |

**Não verificado:**
- O serviço no ROS: o notebook não tem ROS, então o `no_patrulha.py` só foi compilado e lido. A prova é a checagem manual abaixo.
- A ação `voltar-doca` do `lab.sh` (só sintaxe conferida; o `shellcheck` não está instalado).
- O comportamento da Create 3 ao cancelar o destino e logo receber o `dock` (é o mesmo fluxo do PAT-06, já provado no L1).
- `ruff` e `actionlint`: não estão instalados aqui; rodam no CI.
- Sem cenário L1 nesta versão: o SIM-04 continua com os 11 cenários.

**Checagem manual no PC do laboratório (depende da V1 e da fumaça do Gazebo):**
1. `infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz` e `infra/docker/lab.sh sim patrulha`.
2. Com o robô em ronda, em outro terminal: `infra/docker/lab.sh sim voltar-doca`.
3. Esperado no log JSONL (`workspace/logs/`): `doca_pedida`, `destino_cancelado`, `destino_enviado` (aproximação), `dock_ok`, `encerrado` com o detalhe `voltar_doca`, e o código de saída 0 no `resumo`. A resposta do serviço é `success=True`.
4. No robô real, só depois da V5 e com a permissão do Roberto, com a pessoa de segurança ao lado.

## 5. Efeito prático

O operador passa a ter um comando para encerrar a patrulha com o robô encaixado, em vez de parar com Ctrl+C no meio do corredor. A regra "não mande `dock` por fora" continua valendo: a decisão não enxerga esse dock, e a Create 3 recusa o dock se já estiver encaixada. Para a banca: o requisito tem ID, a decisão é testada sem ROS em milissegundos, e o que depende de simulador ou robô está escrito como não verificado.

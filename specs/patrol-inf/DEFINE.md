# DEFINE: requisitos da patrulha no TurtleBot 4 do INF

**Status:** Aprovado em 2026-11-10 (portão da skill `/sdd`). Revisado em 2026-11-10, a pedido do Roberto: entram o PAT-21 (limites relativos), o tempo do PAT-18 por ambiente, o relógio dos tempos-limite e o TST-08 (Gazebo). Na mesma data, corrigido pelo crítico EARS (segunda rodada): entram o PAT-18b, o PAT-21b, o PAT-22, o código 9, a sequência de início e o campo `t_parede`, e foram reescritos o PAT-18, o PAT-21, o VAL-04, o AMB-01, o OBS-03, o TST-03 e o TST-08.
**Data:** 2026-11-10
**Base:** `BRAINSTORM.md` desta pasta

## Resposta direta

Os requisitos abaixo dizem **o que** a nossa patrulha deve fazer, em frases testáveis (formato EARS). O **como** fica no `DESIGN.md`. Cada requisito tem um ID, e o DESIGN liga cada ID ao teste que o prova. O que é procedimento de pessoas (segurança e preparo no INF) fica no protocolo, no fim deste arquivo, e não nos requisitos.

## Termos

| Termo | Significado |
|---|---|
| Sistema | O nosso nó de patrulha (`patrulha_tb4`), e não o `patrol_loop` oficial |
| Configuração | O arquivo YAML da patrulha (pontos, pose inicial, aproximação da doca, limites e tempos) |
| Ambiente | `leve` (nav2_loopback_sim), `gazebo` ou `real` (robô do INF) |
| Limites de bateria | Números com `0 < critica < baixa < alta ≤ 1`. O modo vem de `bateria.modo`: `absoluto` (o padrão, se o campo faltar) ou `relativo` (PAT-21). Valores padrão do modo absoluto: 0,10, 0,20 e 0,95, os mesmos do oficial |
| Tempos-limite | Os tempos da seção `tempos` da configuração (PAT-03, PAT-06, PAT-09, PAT-18, PAT-19 e PAT-20) contam no relógio do ROS. No `leve` e no `gazebo`, esse relógio é o tempo simulado (AMB-02). Exemplo ilustrativo: a 0,18 do tempo real, 30 s simulados levam cerca de 165 s de tempo de relógio, e a 0,10, cerca de 300 s. As exceções são o PAT-15 e o PAT-22, que contam em tempo de relógio, porque precisam valer mesmo se o tempo simulado parar |
| Tempo de relógio | O tempo real, de parede. É nele que contam os prazos do TST-01, do TST-03 e do TST-08, e o campo `t_parede` do log |
| Na doca / fora da doca | Segundo o `is_docked` do último `/dock_status` recebido |
| Sequência de início | 1. `inicio` (OBS-03). 2. VAL-01 a VAL-04 sobre a configuração. 3. PAT-20 e PAT-03 (servidores e primeira bateria), em qualquer ordem. 4. No modo relativo: PAT-21, PAT-21b e a segunda checagem do VAL-04. 5. PAT-17 (primeiro `/dock_status`). 6. Undock |
| Ação ativa | Qualquer destino de navegação, dock ou undock em andamento |
| Destino falho | Destino de patrulha cujo resultado do Nav2 é `ABORTED` ou `FAILED`, ou que estourou o tempo do PAT-19. **Os cancelamentos feitos pelo próprio sistema (PAT-06, PAT-14, PAT-15 e PAT-18) não contam** |
| Volta | Uma passagem por todos os pontos da lista, em ordem, cada um com resultado de sucesso ou de destino falho |
| Ciclo de recarga | Sair da doca, visitar pelo menos 2 pontos, ir à doca por bateria baixa, dock confirmado (PAT-09), carregar até `alta`, undock e chegar com sucesso a mais 1 ponto |
| Evento | Linha do log JSONL. A lista fechada de eventos e os campos estão no `DESIGN.md`, seção "Esquema do log" |

Os valores entre colchetes, como `[30 s]`, são **padrões propostos** e ficam na configuração. Os números do INF ainda precisam ser confirmados com o coordenador.

### Códigos de saída

| Código | Motivo | Evento |
|---|---|---|
| 0 | Encerramento pedido (SIGINT ou SIGTERM) | `encerrado` |
| 2 | Configuração ou pose inválida (VAL) | `config_invalida` |
| 3 | Sem leitura de bateria: no início (PAT-04) ou na doca (PAT-18b) | `sem_bateria` ou `bateria_perdida` |
| 4 | Dock falhou depois de todas as tentativas (PAT-11) | `dock_falhou` |
| 5 | Undock falhou (PAT-16) | `undock_falhou` |
| 6 | Iniciou fora da doca (PAT-17) | `fora_da_doca` |
| 7 | Parou por destinos falhos seguidos, já na doca (PAT-08) | `falhas_seguidas` |
| 8 | Servidor de ação indisponível (PAT-20) | `servidor_indisponivel` |
| 9 | Sem `/clock` no `leve` ou no `gazebo` (PAT-22) | `sem_relogio` |

## PAT: patrulha

- **PAT-01** (Ubiquitous): O sistema DEVE ler os pontos de patrulha, a pose inicial, a pose de aproximação da doca, os limites de bateria e os tempos-limite somente da configuração.
- **PAT-03** (Event-driven): QUANDO o sistema iniciar ENTÃO o sistema DEVE aguardar a primeira mensagem de `/battery_state` por até `[30 s]` antes de enviar qualquer ação.
- **PAT-04** (Unwanted): SE nenhuma mensagem de `/battery_state` chegar dentro do tempo-limite do PAT-03 ENTÃO o sistema NÃO DEVE enviar nenhuma ação, e DEVE encerrar com o código 3.
- **PAT-05** (State-driven): ENQUANTO um destino de navegação estiver em andamento o sistema DEVE comparar a última bateria recebida com os limites pelo menos 1 vez por segundo.
- **PAT-06** (Event-driven): QUANDO o sistema receber uma bateria abaixo de `baixa` e igual ou acima de `critica`, com um destino **de patrulha** em andamento, ENTÃO o sistema DEVE pedir o cancelamento desse destino e enviar o destino de aproximação da doca em até `[2 s]`, contados do recebimento da mensagem.
- **PAT-07** (Event-driven): QUANDO um destino de patrulha terminar como destino falho ENTÃO o sistema DEVE gravar o evento `destino_falhou`, com o índice do ponto e o código do resultado.
- **PAT-07b** (Event-driven): QUANDO um destino falho não completar a sequência do PAT-08 ENTÃO o sistema DEVE enviar o próximo ponto da lista.
- **PAT-08** (Event-driven): QUANDO o `[3º]` destino falho seguido ocorrer ENTÃO o sistema DEVE ir à aproximação da doca, fazer o dock e encerrar com o código 7 depois do dock confirmado. O contador zera a cada destino com sucesso e a cada recarga completa.
- **PAT-09** (Event-driven): QUANDO a ação de dock devolver o resultado ENTÃO o sistema DEVE gravar `dock_ok` somente se o resultado for `SUCCEEDED` e se chegar um `/dock_status` com `is_docked: true` em até `[5 s]` contados desse resultado. Em qualquer outro caso, DEVE gravar `dock_nao_confirmado`.
- **PAT-10** (Event-driven): QUANDO o sistema gravar `dock_nao_confirmado` ENTÃO o sistema DEVE enviar de novo o destino de aproximação da doca e repetir o dock, até `[3]` tentativas no total.
- **PAT-11** (Event-driven): QUANDO as tentativas do PAT-10 se esgotarem ENTÃO o sistema DEVE encerrar com o código 4, sem enviar novas ações.
- **PAT-12** (State-driven): ENQUANTO o robô estiver na doca com a bateria abaixo de `alta` o sistema NÃO DEVE enviar destinos de navegação nem undock.
- **PAT-13** (Event-driven): QUANDO a bateria atingir `alta` com o robô na doca depois de uma ida por bateria (PAT-06, PAT-14 ou PAT-18) ENTÃO o sistema DEVE executar o undock e reenviar **o mesmo ponto** que estava em andamento quando foi à doca.
- **PAT-14** (Event-driven): QUANDO o sistema receber uma bateria abaixo de `critica` com o robô fora da doca e **sem** estar indo à doca ENTÃO o sistema DEVE cancelar a ação ativa e enviar o destino de aproximação da doca, sem visitar nenhum ponto de patrulha. O PAT-14 prevalece sobre o PAT-06.
- **PAT-15** (Event-driven): QUANDO o sistema receber SIGINT ou SIGTERM ENTÃO o sistema DEVE cancelar a ação ativa, gravar o resumo (OBS-02) e encerrar com o código 0 em até `[3 s]` de tempo de relógio.
- **PAT-16** (Unwanted): SE o undock terminar com um resultado diferente de `SUCCEEDED` ENTÃO o sistema NÃO DEVE enviar destinos de patrulha, e DEVE encerrar com o código 5.
- **PAT-17** (Unwanted): SE o primeiro `/dock_status` recebido informar `is_docked: false` ENTÃO o sistema NÃO DEVE iniciar a patrulha, e DEVE encerrar com o código 6. (Começar na doca é o que garante uma pose inicial conhecida.)
- **PAT-18** (Event-driven): QUANDO passar `bateria_perdida_s` desde a última mensagem de `/battery_state` recebida, com o robô fora da doca, ENTÃO o sistema DEVE gravar `bateria_perdida` uma vez e:
  - se a ação ativa for um destino de patrulha ou o undock, ou se não houver ação ativa, cancelar a ação e enviar o destino de aproximação da doca;
  - se já estiver indo à doca ou encaixando, seguir com isso.

  O evento só volta a ser gravado depois que chegar uma nova mensagem. Padrões de `bateria_perdida_s`:
  - `[10 s]` no `leve`;
  - `[30 s]` no `gazebo`, porque lá a bateria simulada sai a cada 10 s simulados (`DESIGN.md`, seção 1.1);
  - no `real`, pelo menos 3 vezes o maior intervalo entre mensagens medido na etapa 1 do kit de campo.
- **PAT-18b** (Unwanted): SE o robô estiver na doca e já tiver passado `bateria_perdida_s` desde a última mensagem de `/battery_state` ENTÃO o sistema NÃO DEVE enviar novas ações, e DEVE gravar `bateria_perdida` e encerrar com o código 3. Isso cobre também a chegada à doca depois do PAT-18 sem que a bateria tenha voltado.
- **PAT-19** (Event-driven): QUANDO um destino de patrulha passar de `[120 s]` sem terminar ENTÃO o sistema DEVE cancelá-lo e tratá-lo como destino falho.
- **PAT-20** (Event-driven): QUANDO um servidor de ação (`navigate_to_pose`, `dock` ou `undock`) não estiver disponível em até `[30 s]` ENTÃO o sistema DEVE encerrar com o código 8.
- **PAT-21** (Optional): ONDE a configuração tiver `bateria.modo: relativo` o sistema DEVE calcular os limites uma única vez, a partir do `percentage` da primeira mensagem recebida no PAT-03, chamado `b0`: `alta` = `b0` − `delta_alta` `[0,005]`, `baixa` = `b0` − `delta_baixa` `[0,01]` e `critica` = `b0` − `delta_critica` `[0,02]`. Os limites ficam fixos até o fim da execução, e os campos `alta`, `baixa` e `critica` da configuração são ignorados.
  - Para que serve: provocar o ciclo de recarga em minutos onde a bateria cai devagar (no Gazebo e no robô real, hipótese H5).
  - No robô real, os deltas talvez precisem crescer por causa do ruído da leitura, que é desconhecido: a confirmar no INF.
- **PAT-21b** (Optional): ONDE a configuração tiver `bateria.modo: relativo` o sistema DEVE gravar o evento `limites_bateria`, com os campos `b0` e `limites` (`alta`, `baixa` e `critica`), logo depois do cálculo do PAT-21 e antes da segunda checagem do VAL-04.
- **PAT-22** (Unwanted): SE `use_sim_time` for verdadeiro e nenhuma mensagem de `/clock` chegar por `[10 s]` de tempo de relógio, desde o início ou desde a última mensagem, ENTÃO o sistema DEVE cancelar a ação ativa, gravar `sem_relogio` e o resumo (OBS-02), e encerrar com o código 9. (Sem `/clock`, nenhum tempo-limite simulado venceria.)

## VAL: validação da configuração

- **VAL-01** (Event-driven): QUANDO o sistema iniciar ENTÃO o sistema DEVE validar a configuração e cada pose contra o mapa (`.yaml` e `.pgm`) antes de enviar qualquer ação.
- **VAL-02** (Unwanted): SE alguma pose tiver um dos motivos `fora_do_mapa`, `celula_ocupada`, `celula_desconhecida` ou `perto_de_obstaculo` (célula ocupada a menos de `[0,25 m]`) ENTÃO o sistema NÃO DEVE iniciar a patrulha, e DEVE gravar `config_invalida` com o nome da pose e o motivo, e encerrar com o código 2.
- **VAL-03** (Ubiquitous): O sistema DEVE oferecer a validação do VAL-01 também como um comando separado (`validar_pontos`), que roda sem ROS e sem robô.
- **VAL-04** (Unwanted): SE `bateria.modo` tiver um valor diferente de `absoluto` ou `relativo`, ou se os limites não forem números finitos com `0 < critica < baixa < alta ≤ 1`, ENTÃO o sistema NÃO DEVE iniciar a patrulha, e DEVE gravar `config_invalida` com o motivo (`modo_invalido` ou `limites_invalidos`) e encerrar com o código 2. A checagem é feita em dois momentos:
  - no modo `absoluto`, dentro do VAL-01, antes de esperar a bateria;
  - no modo `relativo`, os deltas são checados dentro do VAL-01 (`0 ≤ delta_alta < delta_baixa < delta_critica`), e os limites calculados, logo depois do PAT-21b. Um `b0` NaN gera limites NaN, que não são finitos.

## AMB: ambientes

- **AMB-01** (Ubiquitous): As execuções de aceite em `leve`, `gazebo` e `real` DEVEM registrar o mesmo hash do código do pacote (OBS-03). As diferenças entre elas DEVEM ficar só:
  - nos arquivos de `config/`;
  - nos argumentos de launch;
  - nos programas que sobem ao lado do nó (base falsa, `loopback_simulator` e Gazebo), que não fazem parte do pacote.

  Isso se confere comparando os eventos `inicio` nas evidências.
- **AMB-02** (Optional): ONDE o ambiente for `leve` ou `gazebo` o sistema DEVE usar `use_sim_time: true`, e ONDE o ambiente for `real` DEVE usar `use_sim_time: false`.
- **AMB-03** (State-driven): ENQUANTO nenhum processo `rviz2` estiver rodando o sistema DEVE completar o ciclo de recarga do TST-03.

## OBS: observabilidade

- **OBS-01** (Ubiquitous): O sistema DEVE gravar cada evento da lista fechada do `DESIGN.md` num arquivo JSONL, com os campos obrigatórios do esquema.
- **OBS-02** (Event-driven): QUANDO o sistema encerrar com qualquer código da tabela de códigos de saída ENTÃO o sistema DEVE gravar o evento `resumo`, com as voltas completas, os destinos falhos, os docks confirmados, as tentativas de dock, a bateria mínima e a duração. Uma queda por SIGKILL, crash ou falta de energia fica fora do requisito.
- **OBS-03** (Event-driven): QUANDO o sistema iniciar ENTÃO o sistema DEVE gravar como primeiro evento `inicio`, com a versão do pacote, o hash SHA-256 do código do pacote (os arquivos `.py` instalados, inclusive o launch, sem a pasta `config/`), o hash SHA-256 da configuração, o ambiente e o modelo do robô.

## TST: testes locais

- **TST-01** (Ubiquitous): A suíte `pytest` da lógica (`decisao`, `config`, `pontos` e `registro`) DEVE passar sem ROS instalado e em menos de `[10 s]`.
- **TST-02** (Ubiquitous): Todo ID dos grupos PAT, VAL e OBS marcado como L0 na tabela "Requisito → teste" do `DESIGN.md` DEVE ter pelo menos um teste com o marcador `@pytest.mark.req("<ID>")`, e um script de checagem DEVE falhar se faltar algum.
- **TST-03** (Event-driven): QUANDO o teste L1 (leve com mapa reduzido) rodar ENTÃO o sistema DEVE completar pelo menos 1 ciclo de recarga em até `[15 min]` de tempo de relógio, contados entre os `t_parede` do evento `inicio` e do `destino_ok` que fecha o ciclo.
- **TST-04** (Event-driven): QUANDO a base falsa for configurada para falhar o dock 1 vez ENTÃO o sistema DEVE gravar `dock_ok` na 2ª tentativa, no L1.
- **TST-05** (Event-driven): QUANDO a base falsa derrubar a bateria abaixo de `baixa` no meio de um trecho ENTÃO o sistema DEVE gravar o cancelamento e o envio da aproximação da doca, no L1 (prova do PAT-06).
- **TST-06** (Unwanted): SE a memória livre do notebook for menor que o teto do container mais `[1 GiB]` ENTÃO o script de teste NÃO DEVE subir o container.
- **TST-07** (Event-driven): QUANDO o teste de lint rodar ENTÃO o teste DEVE falhar se algum arquivo de `patrulha_tb4/` (fora de `test/`) chamar `getPoseStamped` ou construir uma pose com números literais. (Prova do PAT-01.)
- **TST-08** (Event-driven): QUANDO o teste L3 rodar (Gazebo `maze` no modo enxuto, `bateria.modo: relativo` e nenhum nó da base falsa) ENTÃO o sistema DEVE completar pelo menos 1 ciclo de recarga em até `[60 min]` de tempo de relógio, contados entre os `t_parede` do `inicio` e do `destino_ok` que fecha o ciclo. A evidência inclui a lista de nós (`ros2 node list`) sem a base falsa, o que mostra que a bateria, a doca e as ações vieram da Create 3 simulada.
  - Portão de projeto (fora da frase EARS): o TST-08 só roda num ambiente aprovado pela medição M-GZ (`DESIGN.md`, seção 3), seja o notebook ou o servidor do INF.
  - Execuções com a base falsa ligada, ou no MVSim, não contam como TST-08.

## INF: aceite no robô real

- **INF-02** (Optional): ONDE o perfil de configuração `inf_devagar` estiver ativo o Nav2 DEVE ter o `velocity_smoother.max_velocity` em x de até `[0,15 m/s]`. (No `turtlebot4_navigation/config/nav2.yaml`, linha 285, o valor atual é 0,26.)
- **INF-03** (Event-driven): QUANDO o teste de aceite rodar no robô real ENTÃO o sistema DEVE completar, nesta ordem, `[2]` voltas e `[1]` ciclo de recarga. O teste é invalidado por qualquer comando manual ao robô ou reposicionamento à mão durante a execução. Uma parada pelo protocolo de segurança também invalida a execução.
- **INF-04** (Ubiquitous): Cada execução no INF DEVE gerar um rosbag e o log JSONL, guardados em `workspace/logs/`.

## Protocolo no INF (procedimentos, fora dos requisitos EARS)

Estes itens são de pessoas, e não do sistema. O crítico apontou que não cabem em EARS. Viram checklist no kit de campo, e cada execução registra nas evidências que eles foram cumpridos.

1. **Antes do primeiro movimento autônomo:** `validar_pontos` passou na configuração do laboratório (era o INF-01).
2. **Segurança:** uma pessoa presente, em condições de parar o robô, durante todo movimento autônomo (era o INF-05). Área livre, e o perfil `inf_devagar` nas etapas de 1 ponto e de patrulha devagar.
3. **Aceite:** os números do INF-03 e da velocidade combinados com o coordenador antes da visita.

## DEVE / NÃO DEVE (resumo)

| DEVE | NÃO DEVE |
|---|---|
| Ler pontos e pose só da configuração (PAT-01, TST-07) | Enviar ações sem leitura de bateria (PAT-04) |
| Olhar a bateria durante o trajeto, e reagir se ela sumir (PAT-05, PAT-18) | Andar enquanto carrega (PAT-12) |
| Confirmar o dock pela ação e pelo `/dock_status` (PAT-09) | Patrulhar depois de um undock que falhou (PAT-16) |
| Voltar à doca na bateria crítica (PAT-14) | Começar fora da doca (PAT-17) |
| Validar a configuração e as poses contra o mapa (VAL-01, VAL-04) | Iniciar com pose ou limites inválidos (VAL-02, VAL-04) |
| Rodar nos três ambientes com a mesma versão (AMB-01) | Subir o container sem folga de memória (TST-06) |
| Gravar o log, o início e o resumo (OBS-01 a OBS-03) | Alterar pacotes oficiais (regra de projeto, `DESIGN.md`) |
| Com `bateria.modo: relativo`, calcular os limites a partir da primeira leitura e gravar `limites_bateria` (PAT-21, PAT-21b) | Rodar o aceite em ambientes com hashes de código diferentes (AMB-01, OBS-03) |
| Encerrar sem bateria na doca, ou sem `/clock` (PAT-18b, PAT-22) | Ficar parado sem evento e sem código de saída |

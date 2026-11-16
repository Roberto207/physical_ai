# Registro de mudanças

Tudo o que foi alterado no projeto, o que foi feito e com que objetivo. A entrada mais nova fica em cima. Cada linha diz também como a mudança foi verificada: "medido" é o que eu rodei e vi; "não verificado" é o que ainda depende de um teste.

## 2026-11-13: fim dos passos 3, 4 e 5 (L1 completo e L1b)

Continuação do dia anterior, com o navegador fechado (4,1 a 4,9 GiB disponíveis) e o Docker ligado pelo Roberto. **Os passos 1 a 6 da spec estão concluídos.** Nada rodou em robô físico.

### Execuções (em `progresso/evidencias/l1/`, todas com o `hash_codigo` `d588709ac9de...`)

| Pasta | Cenário | Veredito | Número medido | Pico de RAM |
|---|---|---|---|---|
| `2026-11-13_11-53-32-ciclo` | Ciclo de recarga (TST-03), com o código corrigido | **Aprovado** | Ciclo em 386 s (limite: 900 s). Dock na 1ª tentativa. Ctrl+C ao resumo em 0,13 s | 656 MiB |
| `2026-11-13_12-00-37-sigint` | Ctrl+C com destino em andamento (PAT-15) | **Aprovado** | Do sinal ao resumo em 0,11 s (limite: 3 s), código 0 | 471 MiB |
| `2026-11-13_12-01-56-dock_falha` | O dock falha 1 vez (TST-04, PAT-09 e PAT-10) | **Aprovado** | `dock_nao_confirmado` e, 2 s depois, `dock_ok` na 2ª tentativa | 444 MiB |
| `2026-11-13_12-05-29-bateria_perdida` | A bateria some no trecho e não volta (PAT-18 e PAT-18b) | **Aprovado** | Perda detectada, volta à doca em 4 s, dock, e código 3 já na doca | 459 MiB |
| `2026-11-13_12-06-31-falhas_seguidas` | (inválida) | O Nav2 não subiu | O nó saiu com o código 8 | 388 MiB |
| `2026-11-13_12-07-52-falhas_seguidas` | Três destinos falhos seguidos (PAT-07, PAT-08 e PAT-19) | **Aprovado** | 3 `destino_falhou` por tempo, dock confirmado e código 7 | 437 MiB |
| `2026-11-13_12-08-42-l1b-sem-carimbo` | L1b, primeira tentativa | **Reprovado** (interrompido) | O robô simulado não andou: 2 destinos estouraram os 120 s | |
| `2026-11-13_12-17-29-l1b` | L1b: o `nav2.yaml` do TurtleBot 4 no leve (H4) | **Aprovado** | Ciclo de recarga em 383 s. Ctrl+C ao resumo em 0,11 s | 468 MiB |

### Mudanças do dia

| # | O que mudou | Arquivos | Objetivo | Como foi verificado |
|---|---|---|---|---|
| 24 | O script do L1 detecta "Aborting bringup" no log do Nav2 e sobe o Nav2 de novo, até 3 vezes, guardando o log da tentativa que falhou | `infra/docker/l1_dentro.sh` | A falha de subida do Nav2 leve se repetiu, desta vez com 4,5 GiB disponíveis. Não é carga do notebook, e invalidava o teste sem culpa do nosso nó | **Não exercitado**: nas 2 execuções feitas depois da mudança, o Nav2 subiu de primeira |
| 25 | No L1b, os parâmetros do Nav2 são montados dentro do container: o `nav2.yaml` oficial inteiro, mais a chave `enable_stamped_cmd_vel: true` para o `loopback_simulator` | `infra/docker/l1_dentro.sh`, `infra/docker/teste_l1.sh` | O arquivo oficial manda a velocidade com carimbo de tempo, e o simulador leve, por padrão, espera sem carimbo. Sem a chave, o robô simulado não sai do lugar. O arquivo oficial não foi alterado | Medido: reprovado sem a chave, aprovado com ela |
| 26 | Registros atualizados | `docs/registro-de-mudancas.md`, `progresso/testes.md`, `progresso/README.md`, `contexto/pendencias.md` | Estado do projeto igual ao medido | |
| 27 | Arquivo de próximos degraus criado, listado no índice do `progresso/README.md` e apontado nas pendências | `progresso/proximos-degraus.md`, `progresso/README.md`, `contexto/pendencias.md` | Pedido do Roberto: registrar num lugar coerente o que vem depois dos passos 1 a 6 (M-GZ e L3, L4 e a revisão das decisões) | |

### Achados do dia

| Achado | O que significa |
|---|---|
| **H4 confirmada, com uma ressalva.** O `nav2.yaml` do TurtleBot 4 funciona com o nosso nó no leve, desde que o simulador leve seja avisado de que a velocidade vem com carimbo de tempo | A ressalva é do simulador, e não do robô: no robô real, quem recebe a velocidade é a Create 3. É também o motivo de o manual pedir `stamped:=true` no teleop do Jazzy (kit de campo, etapa 2) |
| **A falha de subida do Nav2 leve é intermitente e não depende de carga** (2 vezes em 16 subidas, em 12 e 13/nov). O log diz: "Failed to activate local_costmap because transform from base_link to odom did not become available" | Hipótese, não testada: é uma corrida entre a ativação do Nav2 e a pose inicial, que é quem faz o simulador leve começar a publicar a posição. Pode ser a mesma falha de 5/nov. O nosso nó reage certo (código 8) |
| O `falhas_seguidas` provoca a falha pelo tempo-limite (PAT-19) | Um destino **abortado pelo próprio Nav2** continua provado só no L0 |
| Trechos no leve com o `maze`: 7 a 12 s por ponto | O ciclo inteiro leva cerca de 6,5 min, dentro da estimativa de 5 a 15 min do DESIGN |

### O que fica para os próximos pedidos

- Medição M-GZ e L3 (Gazebo `maze`): só com pedido explícito. O `config/gazebo_maze.yaml` já existe e foi validado contra o mapa.
- L4 (robô do INF): seguir `specs/patrol-inf/kit-de-campo.md`. Antes, falta decidir como o notebook fala com o robô (rede do Docker).
- Revisar a tabela "Decisões que tomei onde a spec não dizia", na entrada de 12/nov.
- `git init`: decisão do Roberto.

## 2026-11-12: execução da spec `specs/patrol-inf/` (passos 1 a 6 do DESIGN)

Pedido do Roberto: executar a spec. Escopo combinado: passos 1 a 6. Ficam fora a medição M-GZ, o L3 (Gazebo) e o L4 (robô do INF). Nenhum comando foi enviado a robô físico.

### Resumo do estado (fim da sessão de 2026-11-12)

| Passo do DESIGN | Situação | Evidência |
|---|---|---|
| 1. Base falsa publica `/dock_status` na hora (H2) | **Feito e medido. H2 confirmada** | O `patrol_loop` oficial passou de `Dock succeeded` para `Charging...`, sem o `Robot failed to dock`. Log em `progresso/evidencias/patrol_loop-leve-2026-11-12-h2.log` |
| 2. `decisao`, `config`, `pontos` e `registro` com testes (L0) | **Feito e medido** | 124 testes em 0,3 s, no notebook, sem ROS. 31 requisitos L0 rastreados |
| 3. Nó, launch e L1 | **Parcial** | O ciclo de recarga fechou em 360 s (limite do TST-03: 900 s), com pico de 487 MiB. Falta **repetir** com o código corrigido depois dele (ver "Achados") |
| 4. Falhas injetadas na base falsa | **Parcial**: 5 de 8 cenários aprovados | Aprovados: `queda_bateria` (TST-05), `sem_bateria`, `fora_da_doca`, `sem_servidor` e `sem_relogio`. Faltam `dock_falha` (TST-04), `bateria_perdida`, `falhas_seguidas` e `sigint` |
| 5. L1b com o `nav2.yaml` do TurtleBot 4 | **Pendente** | Cenário `l1b` pronto no script |
| 6. Kit de campo | **Feito** (documento) | `specs/patrol-inf/kit-de-campo.md`. Comandos da documentação oficial, não rodados no robô |

Por que parou: a memória disponível do notebook caiu de 5,1 GiB para menos de 1,4 GiB no meio dos testes (o navegador voltou a ser usado). O `teste_l1.sh` recusou os três cenários seguintes, como manda o TST-06. Para terminar, é preciso ter 3 GiB disponíveis por cerca de 20 minutos.

### Execuções do L1 (todas em `progresso/evidencias/l1/`)

| Pasta | Cenário | Veredito | Número medido | Pico de RAM |
|---|---|---|---|---|
| `2026-11-12_23-11-20-sem_relogio` | Nó com `use_sim_time` e sem simulador (PAT-22) | Aprovado | Código 9 em 10,2 s de relógio | 172 MiB (teto de 512) |
| `2026-11-12_23-19-33-ciclo` | Ciclo de recarga (TST-03) | **Reprovado**, por dois motivos explicados em "Achados" | Ciclo em 360 s; 30 destinos com sucesso antes da bateria baixa | 487 MiB |
| `2026-11-12_23-26-53-queda_bateria` | Bateria cai no meio do trecho (TST-05, PAT-06) | Aprovado | Reação em 0,03 s (limite: 2 s). Ctrl+C ao resumo em 0,01 s (limite: 3 s) | 472 MiB |
| `2026-11-12_23-27-51-fora_da_doca` | Começa fora da doca (PAT-17) | Aprovado | Código 6 em 4,8 s, sem nenhuma ação | 412 MiB |
| `2026-11-12_23-28-21-sem_bateria` | Bateria desligada (PAT-03 e PAT-04) | Aprovado | Código 3 em 30,4 s, sem nenhuma ação | 413 MiB |
| `2026-11-12_23-29-22-sem_servidor` | Sem `/dock` e `/undock` (PAT-20) | Aprovado | Código 8 em 30,6 s | 412 MiB |
| `2026-11-12_23-30-29-sigint` | Ctrl+C no meio do trecho (PAT-15) | **Inválido**: o Nav2 não subiu | O nosso nó saiu com o código 8, que é o certo para essa situação | 395 MiB |

Nenhum processo `rviz2` rodou em nenhuma execução (AMB-03). As execuções a partir de 23:26 têm o mesmo `hash_codigo` (`d588709ac9de...`), que é o do código atual. As duas primeiras têm o hash anterior (`85dc080eb8e0...`), de antes da correção do cancelamento.

### Achados dos testes

| Achado | Causa | O que foi feito |
|---|---|---|
| No primeiro `ciclo`, a ida à doca foi **abortada** pelo Nav2 e só deu certo na 2ª tentativa | O nó pedia o cancelamento do destino e enviava o novo destino logo em seguida. O Nav2 ainda estava cancelando e abortou o pedido novo (`nav2.log`: "Aborting handle") | **Corrigido** em `no_patrulha.py`: o cancelamento agora espera a ação antiga terminar (até 1 s) antes do envio. No `queda_bateria`, rodado depois, o dock saiu na 1ª tentativa |
| No primeiro `ciclo`, o Ctrl+C não gerou `encerrado` nem `resumo` | Erro do **script de teste**, e não do nó: o sinal ia para o `ros2 launch`, que, posto em segundo plano por um script, ignora o SIGINT | **Corrigido** em `l1_dentro.sh`: o sinal vai direto para o nó. No `queda_bateria`, o resumo saiu em 0,01 s. Falta o cenário `sigint`, que prova o cancelamento com um destino em andamento |
| No `sigint`, o Nav2 falhou ao subir: "Failed to activate local_costmap because transform from base_link to odom did not become available" | Não investigado. O notebook estava sob carga (a memória disponível caiu de 5,1 para 1,9 GiB durante a execução). Pode ser a mesma falha intermitente de 5/nov (hipótese) | Nada mudou no código. O nó reagiu como a spec pede (código 8, PAT-20). Repetir com memória livre |
| O `l1_dentro.sh` morria ao carregar o ROS | O `set -u` do bash quebra o `setup.bash` do ROS | **Corrigido**: sem o `-u` |
| O simulador leve publica `/clock` | Lido em `nav2_loopback_sim/loopback_simulator.py` (`publish_clock`, padrão `True`) | Confirma o AMB-02 no leve: o nó roda com `use_sim_time: true` |

### Mudanças, uma a uma

| # | O que mudou | Arquivos | Objetivo | Requisito | Como foi verificado |
|---|---|---|---|---|---|
| 1 | Pasta `docs/` criada, com este registro | `docs/registro-de-mudancas.md` | Pedido do Roberto: registrar tudo o que eu mudar e por quê | | |
| 2 | Pasta `pesquisas/` excluída | `pesquisas/` | Pedido do Roberto. Estava vazia (conferido com `ls -la` antes do `rmdir`) | | Medido |
| 3 | `workspace/meu_ws` renomeada para `workspace/meu_ws.root-vazio`, e uma `meu_ws` nova criada | `workspace/` | A pasta antiga pertencia ao `root` (criada pelo container em 9/nov), e eu não conseguia escrever nela. A antiga só tem uma `src/` vazia. Para apagar a sobra: `docker run --rm -v "$PWD/workspace:/w" physical-ai:jazzy rm -rf /w/meu_ws.root-vazio` | | Medido |
| 4 | Pacote `patrulha_tb4` criado (`ament_python`) | `workspace/meu_ws/src/patrulha_tb4/` (`package.xml`, `setup.py`, `setup.cfg`, `resource/`, `pytest.ini`) | É o pacote nosso que vai para o robô. Antes, `src/` estava vazia | DESIGN, seção 1 | Medido: `colcon build` em 1 s dentro do container, sem erro |
| 5 | Máquina de estados pura da patrulha | `patrulha_tb4/decisao.py` | Toda a decisão numa função sem ROS (`decidir`), para testar em milissegundos os casos difíceis: bateria que cai no meio do trecho, dock que falha, bateria que some, relógio parado | PAT-03 a PAT-22 | Medido: 44 testes em `test/test_decisao.py` |
| 6 | Leitura e conferência da configuração | `patrulha_tb4/config.py` | Pontos, pose inicial, doca, limites e tempos só no YAML. Modo de bateria absoluto ou relativo | PAT-01, PAT-21, VAL-04 | Medido: `test/test_config.py` |
| 7 | Validação das poses contra o mapa, e o comando `validar_pontos` | `patrulha_tb4/pontos.py` | Pegar pose fora do mapa, na parede, em área não mapeada ou colada em obstáculo **antes** de o robô andar. Lê o par `.yaml` + `.pgm` do `map_saver`, que é o formato de um mapa feito por SLAM | VAL-01 a VAL-03 | Medido: `test/test_pontos.py`, com mapas de mentira, e as 4 configurações do pacote aprovadas contra os mapas `maze` e `warehouse` da imagem |
| 8 | Log JSONL com lista fechada de eventos, início e resumo | `patrulha_tb4/registro.py` | Saber depois o que o robô fez e por quê, e qual versão rodou (hash do código e da configuração) | OBS-01 a OBS-03 | Medido: `test/test_registro.py` |
| 9 | Nó ROS da patrulha | `patrulha_tb4/no_patrulha.py` | Ponte com o ROS: lê bateria, doca e relógio numa thread, chama `decidir()` e executa pelo `TurtleBot4Navigator` oficial, sem alterá-lo. Confirma o dock pela ação **e** pelo `/dock_status` | PAT, AMB, OBS | Medido no L1: 5 cenários aprovados e o ciclo de recarga fechado. Faltam 4 cenários e a repetição do ciclo |
| 10 | Launch da patrulha | `launch/patrulha.launch.py` | Argumentos `config`, `ambiente` e `use_sim_time`. Não abre o RViz | AMB-01 a AMB-03 | Medido no L1: sobe o nó, e nenhum `rviz2` roda |
| 11 | Suíte L0, lint de poses e checagem de rastreio | `test/` (`conftest.py`, 6 arquivos `test_*.py`, `checar_rastreio.py`) | Provar a lógica sem ROS e garantir que todo requisito L0 tem teste | TST-01, TST-02, TST-07 | Medido: `124 passed in 0.35s`; `checar_rastreio.py` diz "OK: os 31 requisitos L0" |
| 12 | Modelo de configuração do laboratório, sem pontos | `config/inf_lab.yaml` | Arquivo a preencher no INF depois do SLAM | Protocolo, item 1 | Medido: `validar_pontos` recusa o modelo vazio (`campo_faltando: pontos`, código 2), como deve |
| 13 | Base falsa: `/dock_status` publicado na hora do dock e do undock | `infra/tools/fake_tb4_base.py` | Decidir a hipótese H2 (o falso `Robot failed to dock` viria do atraso de até 1 s da base falsa) | PAT-09 | Medido: `patrol_loop` oficial rodado de novo, com `Charging...` logo depois de `Dock succeeded`. **H2 confirmada** |
| 14 | Base falsa: parâmetros para provocar falhas | `infra/tools/fake_tb4_base.py` | `falhar_dock_n`, `queda_bateria_em_s`, `queda_bateria_para`, `parar_bateria_em_s`, `comecar_na_doca`, `simular_bateria`, `simular_doca`, `simular_amcl`. Com os padrões, o comportamento antigo não muda | TST-04, TST-05, PAT-04, PAT-17, PAT-18, PAT-20 | Medido: `queda_bateria_em_s`, `comecar_na_doca`, `simular_bateria` e `simular_doca`. **Não verificado**: `falhar_dock_n` e `parar_bateria_em_s` |
| 15 | Script do teste L1, por cenário | `infra/docker/teste_l1.sh`, `infra/docker/l1_dentro.sh` | Rodar o nosso nó no simulador leve, guardar as evidências (JSONL, logs, pico de RAM) e dar o veredito. Recusa subir sem folga de memória | TST-03 a TST-06, AMB-03 | Medido: 7 execuções (tabela acima). A recusa do TST-06 funcionou 4 vezes, com 1,8 a 1,9 GiB disponíveis |
| 16 | Conferidor de evidências | `infra/tools/conferir_l1.py` | Ler o JSONL de uma execução e dizer se o cenário passou (ordem dos eventos, código de saída, prazos do TST-03, do PAT-06 e do PAT-15) | TST-03 a TST-05 | Medido com logs gerados pelo mundo simulado dos testes: 8 cenários aprovados e 1 controle negativo reprovado, como esperado |
| 17 | Kit de campo | `specs/patrol-inf/kit-de-campo.md` | As 10 etapas no laboratório, com comando, critério de "feito" e link da página oficial | DESIGN, seção 4 | Links conferidos por busca em 2026-11-12. Comandos **não rodados** no robô |

| 18 | Configurações do pacote | `config/leve_reduzido.yaml`, `teste_tempo_curto.yaml`, `gazebo_maze.yaml`, `warehouse_original.yaml` | Pontos curtos (1,5 a 2,5 m) no mapa `maze`, escolhidos lendo o mapa da imagem. A pose inicial (0, 0) é onde o robô nasce encaixado no Gazebo `maze`, então os mesmos pontos servem ao L1 e ao L3. O `warehouse_original` copia os pontos do `patrol_loop` oficial | TST-03, TST-08, AMB-01 | Medido: `validar_pontos` aprovou as 4 contra os mapas oficiais. O `gazebo_maze` e o `warehouse_original` **não foram rodados** |
| 19 | Perfil do Nav2 em velocidade reduzida | `config/nav2_inf_devagar.yaml` | Cópia do `nav2.yaml` oficial com o `velocity_smoother` em 0,15 m/s (era 0,26) | INF-02 | Medido: `diff` mostra só as 2 linhas mudadas, e há um teste na suíte L0. **Não rodado** com o Nav2 |
| 20 | Cancelamento espera a ação antiga terminar | `patrulha_tb4/no_patrulha.py` | Evitar que o Nav2 aborte o destino da doca enviado logo depois do cancelamento (achado do L1) | PAT-06 | Medido: no `queda_bateria`, dock na 1ª tentativa e reação em 0,03 s |
| 21 | Pasta `workspace/meu_ws.root-vazio` apagada | `workspace/` | Era a sobra da mudança 3. Conferi que só tinha a `src/` vazia antes de apagar | | Medido |
| 22 | Evidências do passo 1 e do L1 | `progresso/evidencias/patrol_loop-leve-2026-11-12-h2*.log`, `progresso/evidencias/l1/` | Guardar o que foi observado | INF-04 (mesmo padrão) | |
| 23 | Documentos de progresso atualizados | `progresso/README.md`, `progresso/testes.md`, `progresso/patrol-loop.md`, `contexto/pendencias.md`, `como_rodar.md` | Deixar o estado do projeto igual ao que foi medido | | |

### Decisões que tomei onde a spec não dizia (para o Roberto revisar)

A spec foi seguida. Nestes pontos ela não tinha resposta, e eu escolhi o caminho mais cauteloso. Nenhum arquivo da spec foi alterado.

| Lacuna | O que fiz | Por quê |
|---|---|---|
| O PAT-17 não diz o que fazer se **nenhum** `/dock_status` chegar | Depois de `servidor_s` (30 s), encerra com o código 8 e o detalhe `dock_status` | O DEFINE proíbe "ficar parado sem evento e sem código de saída" |
| O destino de **aproximação da doca** falha (o Nav2 aborta) | Conta como uma tentativa de dock (`dock_nao_confirmado`, detalhe `aproximacao_falhou`) e tenta de novo, até o limite do PAT-10. Depois, código 4 | Sem isso, o robô ficaria parado longe da doca sem sair do laço |
| O robô sai da doca enquanto carrega, sem a gente mandar | Volta a aproximar e encaixar | O PAT-12 só fala do robô **na** doca |
| Um destino cancelado por alguém de fora (não pelo nosso nó) | Conta como destino falho | A definição só exclui os cancelamentos feitos pelo próprio sistema |
| O PAT-18 diz "grava uma vez", e o PAT-18b diz "grava e encerra" | Na doca, grava de novo com o detalhe `na_doca`, e encerra com o código 3 | O evento de saída precisa aparecer no log, junto do código |
| Campos do evento `resumo` | Acrescentei `voltas`, `destinos_falhos`, `docks_confirmados`, `tentativas_dock`, `bateria_minima`, `duracao_s` e `codigo_saida`, só no `resumo` | O OBS-02 exige esses números, mas a tabela de campos do DESIGN não os lista. Sugestão: incluir na tabela |
| Cinza 205 no mapa (o valor que o `map_saver` grava para "não mapeado") | Sempre conta como célula desconhecida | Com `free_thresh: 0.25`, a conta pura do `map_server` leria 205 como livre (ocupação de 0,196). Na dúvida, o robô não vai para lá. **A conferir** com os mapas reais |
| Prova do prazo de 2 s do PAT-06 | Os eventos `bateria_baixa` e `bateria_critica` levam no `detalhe` a idade da mensagem de bateria, e o `destino_enviado` só é gravado depois que o pedido saiu | Sem isso, o log não permitiria medir o tempo de reação |
| Informação nova do Roberto: os mapas serão feitos por nós (SLAM ou outro método) | O `validar_pontos` lê o formato do `map_saver`, o caminho do mapa fica só na configuração (pode ser relativo ao arquivo), e o kit de campo traz a etapa de SLAM | O código não pode depender de um mapa pronto |

### O que faltava no fim de 12/nov (tudo feito em 13/nov, ver a entrada acima)

Tudo abaixo depende de uma coisa só: **3 GiB de memória disponível por cerca de 20 minutos** (navegador fechado). O Docker já está ligado.

| Item | Comando |
|---|---|
| Repetir o ciclo de recarga com o código atual (TST-03) | `infra/docker/teste_l1.sh ciclo` |
| Dock que falha 1 vez (TST-04) | `infra/docker/teste_l1.sh dock_falha` |
| Bateria que some, fora e dentro da doca (PAT-18 e PAT-18b) | `infra/docker/teste_l1.sh bateria_perdida` |
| Três destinos falhos seguidos (PAT-07, PAT-08 e PAT-19) | `infra/docker/teste_l1.sh falhas_seguidas` |
| Ctrl+C com destino em andamento (PAT-15) | `infra/docker/teste_l1.sh sigint` |
| L1b: o `nav2.yaml` do TurtleBot 4 no leve (H4) | `infra/docker/teste_l1.sh l1b` |

Ainda não coberto por nenhum cenário: um destino **abortado pelo próprio Nav2** (o `falhas_seguidas` provoca a falha pelo tempo-limite do PAT-19, e não por um ponto inalcançável). O caminho está provado no L0.

### Não feito, de propósito

- `git init`: recomendado no DESIGN, mas é decisão do Roberto, e ele não aprovou.
- Medição M-GZ e L3: só com pedido explícito.
- Qualquer coisa no robô físico.
- Alterar os arquivos da spec (`BRAINSTORM.md`, `DEFINE.md`, `DESIGN.md`): passaram por portão de aprovação.

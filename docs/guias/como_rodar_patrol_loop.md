# Como rodar o patrol_loop (a nossa patrulha, `patrulha_tb4`)

Escrito em 2026-11-19. Cobre o simulador (Gazebo, degrau L3) e o robô real (kit de campo, etapas 7 a 10). **Nada daqui foi rodado ainda no Gazebo do PC do lab nem no robô.** A fonte dos passos do robô é `specs/patrol-inf/kit-de-campo.md`; a das ações do script é `infra/docker/lab.sh`.

O "patrol_loop" aqui é o nó `patrulha` do pacote `patrulha_tb4`, e não o `patrol_loop.py` oficial do `turtlebot4_python_tutorials`. Ele anda entre pontos, monitora a bateria, volta à doca para carregar e sai de novo. Quem decide é `decisao.py` (máquina de estados pura); `no_patrulha.py` é só a ponte com o ROS.

## Resposta direta

Pré-requisito comum: mapa salvo, pontos escolhidos e `validar_pontos` com `APROVADA`. Depois:

| | Simulador (PC do lab) | Robô real (PC do lab) |
|---|---|---|
| Subir | `lab.sh sim subir gazebo localizacao nav2 rviz` | `MAPA=/mapas/<mapa>.yaml lab.sh robo subir localizacao nav2 rviz` |
| Pose inicial | automática (AMCL do sim) | "2D Pose Estimate" no RViz, na doca |
| Rodar | `lab.sh sim patrulha` | `CONFIG=/mapas/<config>.yaml lab.sh robo patrulha` (pede `SIM`) |
| Parar | `Ctrl+C` | `Ctrl+C` |
| Log | `workspace/logs/*.jsonl` | `workspace/logs/*.jsonl` |

O robô **começa na doca**. A patrulha faz o `undock` sozinha; começar fora da doca termina com código 6.

## 1. Pré-requisitos

| Item | Comando | Pronto quando |
|---|---|---|
| L0 | `cd workspace/meu_ws/src/patrulha_tb4 && python3 -m pytest -q` | sem falhas |
| L1 | `infra/docker/teste_l1.sh ciclo` | APROVADO |
| Imagens Humble | `docker run --rm physical-ai:robo printenv ROS_DISTRO` | `humble` |
| Mapa salvo | `workspace/mapas/<nome>.yaml` e `.pgm` | `conferir_mapa` disse UTILIZÁVEL |
| Config preenchida | `validar_pontos workspace/mapas/<config>.yaml` | `APROVADA` |

O `validar_pontos` não usa ROS nem robô. Recusa pose fora do mapa, em célula ocupada, em área não mapeada ou a menos de 0,25 m de obstáculo. É o item 1 do protocolo: sem ele, nenhum movimento autônomo.

## 2. O arquivo de configuração

Fica ao lado do mapa, em `workspace/mapas/`, que o container enxerga como `/mapas/`. O campo `mapa:` é relativo ao arquivo, então funciona igual no container e no notebook.

```yaml
patrulha:
  ambiente: real                # real | gazebo | leve
  modelo: standard              # standard | lite
  mapa: lab_teste.yaml          # sem caminho: relativo ao arquivo
  pose_inicial: {x: 0.0, y: 0.0, yaw_graus: 0}       # onde o robô fica encaixado
  aproximacao_doca: {x: 0.0, y: 0.0, yaw_graus: 0}   # de frente para a doca, 0,5 a 1 m
  pontos:
    - {x: 1.5, y: 0.0, yaw_graus: 0}                 # na primeira rodada, só 1 ponto, perto da doca
  bateria: {modo: absoluto, alta: 0.95, baixa: 0.20, critica: 0.10}
  tempos: {bateria_perdida_s: 30, espera_bateria_s: 30, confirma_dock_s: 5, destino_s: 120, servidor_s: 30}
  limites: {falhas_seguidas: 3, tentativas_dock: 3}
  validacao: {margem_obstaculo_m: 0.25}
```

Dois erros comuns: `mapa:` com caminho absoluto do notebook, e `bateria_perdida_s` abaixo de 3 vezes o maior intervalo medido do `/battery_state` (PAT-18; em 2026-11-16 a bateria chegava a 0,2 Hz, então no mínimo 15 s).

## 3. No simulador (L3)

```bash
infra/docker/lab.sh sim parar                                   # mundo limpo, robô encaixado
infra/docker/lab.sh sim subir gazebo localizacao nav2 rviz
infra/docker/lab.sh sim logs gazebo                             # espere cerca de 1 min
infra/docker/lab.sh sim patrulha                                # usa gazebo_maze.yaml; CONFIG=... troca
```

- Não suba o `slam` junto: ele e a `localizacao` publicam a transformação `map → odom`.
- Não faça `undock` nem `teleop` antes.
- Sem `MAPA`, a `localizacao` usa o `maze` do pacote `turtlebot4_navigation`, o mesmo do `gazebo_maze.yaml`. Se passar `MAPA=` de outro mapa, o `validar_pontos` e o Nav2 passam a usar mapas diferentes.
- A bateria simulada cai devagar e só é publicada a cada 10 s simulados; o ciclo de recarga leva minutos. É por isso que o `gazebo_maze.yaml` usa o modo `relativo`.

## 4. No robô real

Regras que valem o tempo todo: uma pessoa ao lado do robô, pronta para pará-lo; área livre; velocidade de 0,15 m/s (o serviço `nav2` já usa `nav2_inf_devagar.yaml`); só imagens Humble (o `lab.sh` recusa outra, SEG-01); não usar o modo `robo` até a V5 de `specs/migracao-humble/` passar. Nenhum comando fora do kit sem combinar antes.

1. **Rede.** `infra/docker/lab.sh robo checar-rede` precisa dizer `REDE OK`. O robô usa Discovery Server (id 1, porta 11811), domínio 0, namespace `/robot1`. Se o IP mudou, edite só o `ROS_DISCOVERY_SERVER` de `infra/lab/rede_lab.env`. Não altere a rede do robô.
2. **Robô na doca**, doca na tomada, batendo com a `pose_inicial` da config.
3. **Nada do `sim` rodando:** `infra/docker/lab.sh sim parar`.
4. **Subir localização e Nav2:**

   ```bash
   infra/docker/lab.sh robo compose stop slam
   MAPA=/mapas/lab_teste.yaml infra/docker/lab.sh robo subir localizacao nav2 rviz
   ```

5. **Pose inicial.** No RViz, "2D Pose Estimate" na posição e orientação reais da doca. Confira que o lidar coincide com as paredes do mapa. Se não coincidir, o AMCL está desalinhado e o robô vai navegar para o lugar errado. Corrija antes de seguir. Opcional: um "Nav2 Goal" próximo, com a pessoa de segurança pronta.
6. **Rodar:**

   ```bash
   CONFIG=/mapas/inf_lab_preenchido.yaml infra/docker/lab.sh robo patrulha
   ```

   O serviço compila o pacote, roda o `validar_pontos`, pede que se digite `SIM` e só então sobe o nó. Sem `CONFIG`, ele usa `inf_lab.yaml` (o modelo vazio), que recusa de propósito.

### Escada de etapas no robô

| Etapa | O que muda | Pronto quando |
|---|---|---|
| 7. 1 ponto | Só 1 ponto, perto da doca. `Ctrl+C` depois de 2 ou 3 idas | log com `undock_ok`, pelo menos 2 `destino_ok`, e `encerrado` e `resumo` gravados |
| 8. Volta completa | Lista completa, `validar_pontos` de novo | 1 volta, todos com `destino_ok` |
| 9. Recarga | `bateria: modo: relativo` (volta à doca com queda de 1 ponto percentual, sai com recuperação de 0,5) | log com `bateria_baixa`, `dock_ok`, `carga_completa`, `undock_ok`, `destino_ok`, nesta ordem |
| 10. Aceite | Rosbag gravando, sem intervenção (comando no kit de campo, etapa 10) | 2 voltas e 1 ciclo, ou o combinado com o coordenador |

Se a leitura da bateria oscilar e o robô voltar cedo demais à doca, aumente `delta_baixa` e `delta_critica`, mantendo `delta_alta < delta_baixa < delta_critica`. Qualquer comando manual, reposicionamento ou parada de segurança invalida a execução de aceite (INF-03).

## 5. O que a patrulha faz (fases)

`iniciando → saindo_doca → patrulhando → indo_doca → encaixando → carregando`, e `encerrando` no fim.

1. Começa encaixada na doca (senão, código 6).
2. `undock` e vai ao primeiro ponto.
3. Percorre os pontos em loop.
4. Com a bateria abaixo do limite "baixa", ou 3 falhas seguidas de destino, cancela o destino, vai ao ponto de aproximação da doca e faz `dock`. O `dock` só vale se a ação terminar com sucesso **e** o `/dock_status` disser `is_docked: true`; se falhar, reaproxima e tenta de novo até `tentativas_dock` vezes.
5. Carrega até o limite "alta", faz `undock` e volta ao loop.
6. `Ctrl+C` cancela a ação em andamento, grava o resumo e sai em até 3 s (PAT-15).

## 6. Códigos de saída e diagnóstico

| Código | Significado | Onde olhar |
|---|---|---|
| 0 | Encerrado normalmente | log `resumo` |
| 2 | Configuração inválida | mensagem do `validar_pontos` |
| 3 | Sem bateria | `lab.sh <modo> logs`, tópico `battery_state` |
| 4 | Falha no dock | `dock_status`, pose de `aproximacao_doca` |
| 5 | Falha no undock | doca energizada? robô encaixado? |
| 6 | Começou fora da doca | reposicione à mão, ou `sim parar` e `subir` |
| 7 | Falhas seguidas de destino | `logs nav2` e `logs localizacao`; pose inicial |
| 8 | Servidor de ação indisponível | Nav2 não subiu; `logs nav2` |
| 9 | Sem relógio (`/clock`) | sim: Gazebo não subiu; real: `use_sim_time` |

O log JSONL (um evento por linha, com resumo e hash do código) fica em `workspace/logs/`. Antes de mexer no `decisao.py`, leia o log.

## Efeito prático

O que prova o checkpoint 2 é um ciclo completo (sai, patrulha, volta, encaixa, carrega, sai de novo) com o log como evidência, primeiro no Gazebo e só depois no robô. O ponto de maior risco no robô é a pose inicial do AMCL: com ela errada, tudo o mais parece funcionar e o robô vai ao lugar errado.

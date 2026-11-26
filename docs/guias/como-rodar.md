# Como rodar no robô real

Todos os comandos rodam no PC do laboratório, na raiz do repositório. O robô é escolhido por `ROBO` (`robot1`, o padrão, ou `robot3`). Os IPs e servidores de descoberta de cada um ficam em `scripts/env.sh`.

**[move]** marca o que move o robô. Rode esses comandos só com uma pessoa ao lado, capaz de pará-lo.

## 0. Uma vez por PC

```bash
docker build -t physical-ai docker/        # imagem: ROS 2 Humble + TurtleBot 4 + RViz
systemctl is-active ollama                 # o LLM precisa do Ollama no PC: "active"
ollama pull qwen2.5:1.5b                   # o modelo usado
```

Rotas: o `scripts/checar.sh` avisa se o PC não tem as rotas 192.168.185.0/24 e 192.168.186.0/24 pelo IP do robô, e mostra o comando. O porquê está em `docs/guias/acesso-ao-robo.md`.

## 1. Conferir a rede (não move)

```bash
export ROBO=robot3
scripts/checar.sh                          # precisa terminar em APROVADO
```

A skill `/preflight-robo` do Claude Code faz este passo e os passos 2 e 3, item por item.

## 2. Localização e pose

Antes deste passo: robô na doca e área livre.

```bash
scripts/subir.sh                           # AMCL no mapas/mapa_lab_novo + RViz
docker logs -f tb_localizacao              # espere "Managed nodes are active" (cerca de 1 min)
```

No RViz, use o **2D Pose Estimate** na posição e na direção reais do robô. O laser precisa cair sobre as paredes.

## 3. Nav2

```bash
scripts/subir.sh nav2
docker logs -f tb_nav2                     # espere "Managed nodes are active", sem "Aborting" depois
```

Esta é a ordem que funcionou no robô em 25/11: localização, pose, Nav2. Se o Nav2 abortar, rode `scripts/subir.sh nav2` de novo; ele recria só o Nav2.

## 4. Patrulha **[move]**

```bash
scripts/patrulha.sh --verificar-localizacao voltas 1   # confere doca, pose e Nav2, sem mover
scripts/patrulha.sh voltas 1               # undock, 1→2→3→4, doca  (0 = voltas até Ctrl+C)
scripts/patrulha.sh ida-e-volta            # undock, 1,2,3,4,3,2,1, doca
scripts/patrulha.sh continuo               # undock, 1, depois 3→4→3→1 até Ctrl+C ou bateria baixa
scripts/patrulha.sh doca                   # só volta ao ponto 1 e encaixa (depois de uma interrupção)
```

**Antes de começar, a patrulha exige:**

- o robô na doca (exceto em `doca`);
- `map→odom` recente;
- as ações de navegação, dock e undock disponíveis;
- bateria de 20% ou mais.

**Durante a patrulha:**

- abaixo de 20% de bateria, ela volta à doca;
- cada ponto tem 120 s, e um ponto que falha interrompe a patrulha onde o robô estiver;
- `Ctrl+C` cancela a meta, mas não leva o robô de volta à doca.

| Código de saída | Significado |
|---|---|
| 0 | Rota concluída e dock confirmado (ou só verificação) |
| 2 | Robô não confirmado na doca |
| 3 | Bateria ausente ou abaixo de 20% |
| 4 | Undock não confirmado |
| 5 | Falha na volta à doca |
| 6 | Um ponto falhou, foi recusado ou passou de 120 s |
| 7 | Sem `map→odom` recente: refaça o 2D Pose Estimate |
| 8 | Ações do Nav2, dock ou undock indisponíveis |
| 130 | Interrompido (`Ctrl+C` ou `scripts/parar.sh`) |

Só `voltas` tem ensaio no robô. `ida-e-volta`, `continuo` e `doca` repetem rotas que nunca rodaram fisicamente.

## 5. Comandos por LLM

Passo a passo e limites em `docs/guias/llm.md`. Em resumo:

- `scripts/llm.sh` sobe o LLM com freio: interpreta e não move.
- `scripts/llm.sh mover` **[move]** faz o robô andar a cada pedido.
- Os pedidos são escritos em outro terminal, com `scripts/falar.sh`.

A patrulha e o LLM sem freio não rodam juntos: cada script recusa se o outro estiver no ar.

## 6. Encerrar (sempre)

```bash
scripts/parar.sh                           # cancela a meta do LLM e da patrulha e remove os contêineres
docker ps                                  # não deve sobrar nenhum "tb_..."
```

## 7. Mapa novo

```bash
scripts/mapa.sh                            # SLAM + RViz (não move)
scripts/teleop.sh                          # [move] outro terminal: dirigir a 0,15 m/s
scripts/mapa.sh salvar lab_<data>          # grava mapas/lab_<data>.yaml e .pgm
```

Para usar o mapa novo: `MAPA=/work/mapas/lab_<data>.yaml scripts/subir.sh`. Os pontos da patrulha e do LLM precisam ser medidos de novo e trocados em `robo.py` (`DOCA` e `PONTOS`) e em `mapas/pontos_mapa_lab_novo.md`. O teste `test_pontos_iguais_aos_da_task1` vai falhar de propósito até ser atualizado.

## 8. Comandos avulsos (só leitura)

O `scripts/ros.sh` abre um contêiner temporário, por isso demora alguns segundos.

```bash
scripts/ros.sh ros2 topic list
scripts/ros.sh ros2 topic echo --once /robot3/battery_state sensor_msgs/msg/BatteryState \
    --qos-profile sensor_data --field percentage          # 0.78 = 78%
scripts/ros.sh ros2 topic echo --once /robot3/dock_status irobot_create_msgs/msg/DockStatus \
    --qos-profile sensor_data                             # is_docked, dock_visible
scripts/ros.sh timeout 20 ros2 topic hz /robot3/scan      # cerca de 8 Hz em 25/11
scripts/ros.sh ros2 topic echo /robot3/clicked_point      # coordenadas do Publish Point do RViz
```

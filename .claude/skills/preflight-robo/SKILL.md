---
name: preflight-robo
description: Use antes de a patrulha ou o LLM (sem freio) moverem o TurtleBot 4, ou quando o usuário pedir para conferir se o robô, a rede e o Nav2 estão prontos ("preflight", "posso rodar a patrulha?", "confere o robô antes de rodar"). Só lê e, com OK, sobe serviços no PC; nunca move o robô. Responde APROVADO ou REPROVADO, item por item.
allowed-tools: ["Read", "Bash", "AskUserQuestion"]
---

# Preflight do robô

Confere PC, rede, robô e Nav2 antes de `scripts/patrulha.sh` ou `scripts/llm.sh mover`.
Comandos a partir da raiz do repositório, na conversa principal (nenhum subagente alcança o robô).

**Qual robô:** pergunte antes e ponha `ROBO=<robot1|robot3>` na frente de **todo** script.

## Limites

| Classe | Ações |
|---|---|
| Livre | Ler arquivos, `scripts/checar.sh`, `ping`, `docker ps`, `docker logs`, leitura de tópicos |
| Com OK, um por vez | `scripts/subir.sh rviz`, `scripts/parar.sh` (avise que derruba tudo) |
| Proibido | `patrulha.sh` sem `--verificar-localizacao`, `llm.sh mover`, `teleop.sh`, `falar.sh`, dock/undock, publicar em tópico, `sudo`, mudar rede ou configuração do robô, entrar no robô |

Correção no robô ou com `sudo`: mostre o comando e a página oficial
([Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html),
[Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html));
quem roda é o operador. Item reprovado ou não verificado → **REPROVADO**. Resposta vaga não é OK.

## Ordem

1. **Rede e robô:** `ROBO=<nome> scripts/checar.sh` precisa dar `APROVADO`. Se faltarem tópicos,
   o operador pode rodar **no robô**: `ros2 daemon stop; ros2 daemon start; ros2 topic list`.
2. **Subir, com OK** (pule se `checar.sh` já mostra `tb_localizacao` e `tb_nav2` no ar):
   `ROBO=<nome> scripts/subir.sh rviz`. Espere `Managed nodes are active` em
   `docker logs tb_nav2` e em `docker logs tb_localizacao`.
3. **Pare.** O operador faz o 2D Pose Estimate na pose real da doca e confirma o laser nas paredes.
4. **Estabilidade (1 min):** para `c` em `tb_nav2` e `tb_localizacao`,
   `docker logs --since 1m $c 2>&1 | grep -iE "heartbeat|IS DOWN"` não pode mostrar queda de nó. `bond_timeout` em 120:
   `docker exec tb_nav2 bash -c "source /opt/ros/humble/setup.bash; ros2 param get
   /<robô>/lifecycle_manager_navigation bond_timeout"` (precisa de `ROS_SUPER_CLIENT=True` se não achar).
5. **Sem mover:** `ROBO=<nome> scripts/patrulha.sh --verificar-localizacao voltas 1` termina com
   "Localização e Nav2 verificados; nenhum movimento enviado".
6. **Operador**, sem presumir: pessoa ao lado capaz de parar o robô? Área livre? O robô ligado é
   o escolhido? Trajeto de volta à doca livre no costmap?

## Saída

Tabela item → resultado → evidência curta, e o veredito: **APROVADO** só com os 6 itens atendidos.
Com APROVADO, mostre o comando para **o operador** rodar (ex.: `ROBO=<nome> scripts/patrulha.sh
voltas 1`). O veredito vale para aquele momento e **não autoriza movimento**.

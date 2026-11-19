# 2026-11-19: arquivo de estudo do fluxo `lab.sh` até o patrol loop

**Pedido:** sessão de dúvidas sobre o fluxo de comandos, a estrutura e a ideia do projeto, do SLAM (checkpoint 1) ao patrol loop (checkpoint 2): o que fazer, como os comandos existentes fazem isso, o que é dever do Roberto, e os conceitos de ROS, Docker e TurtleBot 4. Começando por `infra/docker/lab.sh sim subir gazebo slam rviz`.

**Resposta direta:** foi escrito `estudo/duvidas/01-do-lab-sh-ao-patrol.md`. Ele fica em `estudo/`, que é pessoal e fora do git (`.gitignore`), então não sobe no push.

**Como foi feito:** leitura de `infra/docker/lab.sh`, `infra/compose/sim.yaml` e `robo.yaml`, `Dockerfile`, `entrypoint.sh`, `infra/lab/rede_lab.env`, `specs/patrol-inf/kit-de-campo.md` e `DESIGN.md`, e do pacote `patrulha_tb4` (`decisao.py`, `config/gazebo_maze.yaml`, `patrulha.launch.py`). Nenhum código foi alterado e nada foi executado.

**Não verificado:** a sequência `lab.sh sim subir gazebo localizacao nav2 rviz` e `lab.sh sim patrulha` no Gazebo (depende da V1 e do teste de fumaça no PC do lab); parâmetros internos do Nav2.

**Efeito prático:** o Roberto tem uma referência única para ler qualquer comando do `lab.sh` (modo, ação, serviços), e para saber o que cabe a ele em cada checkpoint.

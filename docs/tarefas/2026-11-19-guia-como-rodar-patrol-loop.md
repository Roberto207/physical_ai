# 2026-11-19: guia `como_rodar_patrol_loop`

**Pedido:** passo a passo de como rodar o patrol_loop, no simulador e no robô, e depois salvar a explicação em `como_rodar_patrol_loop`.

**Resposta direta:** foi criado `docs/guias/como_rodar_patrol_loop.md`, com pré-requisitos, formato da config, roteiro do Gazebo, roteiro do robô real (etapas 7 a 10 do kit de campo), as fases da patrulha e a tabela de códigos de saída.

**Como foi feito:** leitura de `infra/docker/lab.sh`, `infra/compose/sim.yaml` e `robo.yaml`, `infra/lab/rede_lab.env`, `specs/patrol-inf/kit-de-campo.md`, `config/gazebo_maze.yaml` e `inf_lab.yaml`, `no_patrulha.py` e `estudo/duvidas/01-do-lab-sh-ao-patrol.md`. Nenhum código foi alterado e nada foi executado.

**Não verificado:** toda a sequência no Gazebo do PC do lab e no robô real (depende da V1 e da V5 de `specs/migracao-humble/`).

**Observação:** o `infra/lab/rede_lab.env` ainda diz "Jazzy" no cabeçalho e no comentário do `RMW_IMPLEMENTATION`; o texto está desatualizado (Humble desde 2026-11-18). Não foi alterado.

**Efeito prático:** uma referência única, em `docs/guias/`, para rodar a patrulha sem reler o kit de campo inteiro.

# Decisões do projeto

Registro de decisões já tomadas, com o motivo. Atualizar quando algo mudar.

| Data | Decisão | Motivo | Estado |
|---|---|---|---|
| 2026-11-05 | O notebook do Roberto é cliente; simulação e robô ficam no INF | O notebook tem 7,4 GiB de RAM e GPU integrada. A simulação local rodou a cerca de 18% do tempo real no melhor caso (GPU Intel, sem janela, sem Nav2) | **A confirmar com o coordenador** |
| 2026-11-05 | Padrão técnico provisório: ROS 2 Jazzy, Ubuntu 24.04 em container Docker | O notebook roda Lux (Debian) e o Jazzy é suportado no Ubuntu 24.04. O colega Gabriel usa o mesmo par | Provisório. **Substituída pelo ADR-001** (Humble) em 2026-11-18 |
| 2026-11-05 | Tudo que for pesado no notebook roda em container com limite de memória | Um `docker build` sem limite saturou a RAM e travou o notebook | Em vigor |
| 2026-11-05 | Mapa de estudo de 40 semanas e 8 horas semanais, em `../../estudo/recomendado/` | Prazo de 10 meses e disponibilidade do Roberto | Vale para depois das missões |
| 2026-11-05 | Plano de 6 semanas só com as duas missões, em `../../estudo/` | Prazo de 1 mês e meio informado pelo Roberto: cerca de 48 horas | Em vigor. A confirmar a data exata |
| 2026-11-05 | Decisão da patrulha e validador da LLM em Python puro, testados com `pytest`, separados do ROS | A simulação é lenta no notebook e cada teste nela leva minutos | Em vigor |
| 2026-11-05 | A LLM escolhe entre ações discretas validadas e nada é executado com `exec` | O tutorial oficial executa código gerado pelo modelo | Proposta, a confirmar com a equipe |
| 2026-11-05 | Colab e Kaggle não são usados para simular o robô | O FAQ do Colab restringe acesso remoto e proxies. Possível uso para avaliar LLM em lote | Em vigor |
| 2026-11-09 | O foco do `patrol_loop` e da missão 1 é o simulador leve (`nav2_loopback_sim` com base falsa). O Gazebo vira apoio opcional | Restrições do notebook: Gazebo a cerca de 18% do tempo real e 2,6 GiB com janela. O simulador leve rodou a patrulha completa com cerca de 0,7 GiB | Revisada em 2026-11-10 (linha abaixo). **Substituída pelo ADR-002** (Gazebo principal no PC do lab) em 2026-11-18 |
| 2026-11-10 | O Gazebo `maze` enxuto (sem janela e sem RViz, teto de 3,5 GiB, pontos curtos, limites de bateria relativos, base falsa desligada) passa a ser o degrau L3 recomendado da spec `../../specs/patrol-inf/`. O `warehouse` com Nav2 continua fora. O MVSim fica como plano B | O leve só testa a lógica, porque a bateria, a doca e o AMCL são falsos. O Gazebo é o único teste local com a doca e a bateria da Create 3 simulada (código da iRobot) e com o AMCL de verdade. O código de patrulha é o mesmo nos três ambientes: só mudam a configuração e o launch | Decisão do Roberto. Depende da medição M-GZ (pendente, `DESIGN.md`, seção 3). Se ela reprovar, o L3 vai para o servidor do INF ou para o MVSim |
| 2026-11-18 | Todas as imagens em ROS 2 Humble. O Jazzy fica na tag git `jazzy-final` e nas imagens `physical-ai:jazzy-<alvo>` | Os nós Jazzy do PC derrubaram o robô Humble em 2026-11-16 (`ParticipantEntitiesInfo`) | Aceito: `../../docs/decisoes/ADR-001-ros2-humble.md` |
| 2026-11-18 | O Gazebo (Ignition Fortress) sem janela no PC do lab é o simulador principal. O `nav2_loopback_sim` é vendorizado e continua como L1 de injeção de falhas | O notebook deixou de simular: o PC do lab simula e o robô físico testa | Aceito: `../../docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md` |

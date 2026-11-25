# Decisões do projeto

Registro do que foi decidido e por quê. Atualizar quando algo mudar.

## ADRs (decisões em vigor, com contexto completo)

| ADR | Decisão | Data |
|---|---|---|
| [ADR-001](ADR-001-ros2-humble.md) | Todas as imagens em ROS 2 Humble. O Jazzy fica na tag git `jazzy-final` e nas imagens `physical-ai:jazzy-<alvo>` | 2026-11-18 |
| [ADR-002](ADR-002-gazebo-principal-no-pc-do-lab.md) | O Gazebo (Ignition Fortress) sem janela no PC do lab é o simulador principal. O `nav2_loopback_sim` é vendorizado e continua como L1 de injeção de falhas | 2026-11-18 |

## Decisões de 2026-11-25

| Decisão | Motivo |
|---|---|
| LLM: no dock e na saída da doca a manobra termina e depois obedece; só "parar" cancela | Decisão do operador |
| LLM: usar os clientes de ação do `TurtleBot4Navigator`, sem os atalhos que bloqueiam | Para o "pare" sempre ser atendido |
| LLM sem aprovação humana por ação | Decisão do operador; segue o tutorial |
| LLM: mensagem durante o trajeto cancela a meta e vira a ordem principal | Decisão do operador |
| A LLM segue o tutorial: coordenadas livres, `dock`, `undock` e ignorar pedidos quando ocupado, exceto "parar" | Decisão do operador |
| Skills e subagentes do Claude Code em `.claude/` no repositório | O usuário do PC do laboratório é compartilhado; assim valem só neste projeto e vão pelo git |
| LLM: Ollama com `qwen2.5:1.5b` | Gratuito e local |
| O manual do TurtleBot 4 (Resources) e o `turtlebot4_tutorials` são a primeira consulta ao planejar | O tutorial oficial foi a base da patrulha que funcionou |
| A patrulha no robô usa os programas de `workspace/patrulha_oficial/` e o `mapa_lab_novo` | São os que vêm sendo usados. Os mapas antigos foram apagados |
| Os pontos são os de `workspace/mapas/pontos_mapa_lab_novo.md`, sem os graus | Graus não confirmados |
| Retirada a regra que proibia o `lab.sh robo` até a verificação V5 | Decisão do Roberto. As demais regras de segurança continuam (`docs/contexto/AGENTES.md`, seção 1) |

## Decisões antigas (2026-11-05 a 2026-11-10)

Anteriores aos ADRs. Os caminhos e os números são da época.

| Data | Decisão | Motivo | Estado |
|---|---|---|---|
| 2026-11-05 | O notebook do Roberto é cliente; simulação e robô ficam no INF | O notebook tem 7,4 GiB de RAM e GPU integrada. A simulação local rodou a cerca de 18% do tempo real no melhor caso (GPU Intel, sem janela, sem Nav2) | **A confirmar com o coordenador.** Na prática o PC do lab simula (ADR-002) |
| 2026-11-05 | Padrão técnico provisório: ROS 2 Jazzy, Ubuntu 24.04 em container Docker | O notebook roda Lux (Debian) e o Jazzy é suportado no Ubuntu 24.04. O colega Gabriel usa o mesmo par | **Substituída pelo ADR-001** (Humble) em 2026-11-18 |
| 2026-11-05 | Tudo que for pesado no notebook roda em container com limite de memória | Um `docker build` sem limite saturou a RAM e travou o notebook | Em vigor, só para o notebook (`docs/contexto/AGENTES.md`, seção 4) |
| 2026-11-05 | Mapa de estudo de 40 semanas e 8 horas semanais | Prazo de 10 meses e disponibilidade do Roberto | Vale para depois das missões. O material é local, fora do git |
| 2026-11-05 | Plano de 6 semanas só com as duas missões | Prazo de 1 mês e meio informado pelo Roberto: cerca de 48 horas | Em vigor. A confirmar a data exata. Material local, fora do git |
| 2026-11-05 | Decisão da patrulha e validador da LLM em Python puro, testados com `pytest`, separados do ROS | A simulação é lenta no notebook e cada teste nela leva minutos | Em vigor |
| 2026-11-05 | A LLM escolhe entre ações discretas validadas e nada é executado com `exec` | O tutorial oficial executa código gerado pelo modelo | Proposta, a confirmar com a equipe |
| 2026-11-05 | Colab e Kaggle não são usados para simular o robô | O FAQ do Colab restringe acesso remoto e proxies. Possível uso para avaliar LLM em lote | Em vigor |
| 2026-11-09 | O foco do `patrol_loop` e da missão 1 é o simulador leve (`nav2_loopback_sim` com base falsa). O Gazebo vira apoio opcional | Restrições do notebook: Gazebo a cerca de 18% do tempo real e 2,6 GiB com janela. O leve rodou a patrulha completa com cerca de 0,7 GiB | Revisada em 2026-11-10. **Substituída pelo ADR-002** em 2026-11-18 |
| 2026-11-10 | O Gazebo `maze` enxuto (sem janela e sem RViz, teto de 3,5 GiB, pontos curtos, limites de bateria relativos, base falsa desligada) passa a ser o degrau L3 recomendado da spec `specs/patrol-inf/`. O `warehouse` com Nav2 continua fora. O MVSim fica como plano B | O leve só testa a lógica, porque a bateria, a doca e o AMCL são falsos. O Gazebo traz a doca e a bateria da Create 3 simulada e o AMCL de verdade. O código de patrulha é o mesmo nos três ambientes: só mudam a configuração e o launch | Decisão do Roberto. Depende da medição M-GZ (pendente, `specs/patrol-inf/DESIGN.md`, seção 3) |

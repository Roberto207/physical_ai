# Pendências e dúvidas em aberto

Perguntar ao coordenador (prazo das missões: cerca de 1 mês e meio, a partir de 2026-11-05):
- [ ] **Qual é a data exata de entrega e "pronto" é em simulação ou no robô real?**
- [ ] A missão pode ser dividida na equipe (patrulha e LLM em paralelo)?
- [ ] Qual modelo de TurtleBot (TurtleBot 4 padrão ou Lite) e quantos há no INF?
- [ ] Como reservar/acessar os robôs no INF? Há rede Wi-Fi dedicada?
- [ ] Qual é a plataforma do gêmeo digital (versão do Gazebo? há um repositório?) e quem a mantém?
- [ ] Qual versão do ROS e distro a equipe vai padronizar?
- [ ] Qual provedor de LLM usar (a OpenAI exige chave paga)? O INF/AKCIT tem GPU ou créditos de API?
- [ ] Existe um marco ou entrega intermediária nos 10 meses?
- [ ] O notebook pode ser só cliente? O INF oferece servidor para simulação?
- [ ] Como acessar esse servidor de fora (SSH, VPN, rede do campus)? Há interface gráfica remota?

Testar na minha máquina (ver `infra/teste-simulacao-2026-11-05.md`):
- [x] Simulação sem janela no Docker: cerca de 5% do tempo real com CPU e 18% com GPU Intel
- [x] Janela do Gazebo com GPU Intel: estourou o limite de 2,5 GiB (OOM no container). Em 2026-11-09, com teto de 3,5 GiB e o Opera fechado, funcionou (2,6 GiB)
- [ ] `/battery_state` não entregou mensagem nos testes. Causa provável (2026-11-10, lendo o código): sai a cada 10 s simulados, cerca de 55 s de relógio a 0,18 do tempo real. Confirmar na medição M-GZ
- [ ] **Medição M-GZ (pendente, 2026-11-10):** Gazebo `maze` sem janela, teto de 3,5 GiB, primeiro sem e depois com Nav2. Mede o fator de tempo real, a RAM, a bateria, a doca, o lidar e um destino de 2 m. Decide se o degrau L3 da spec roda no notebook. Plano e critérios em `specs/patrol-inf/DESIGN.md`, seção 3

Verificar:
- [x] Compilar `turtlebot4_python_tutorials` e `turtlebot4_openai_tutorials` do GitHub (não há apt para Jazzy)
- [ ] O robô físico é Lite ou padrão? O launch de topo da simulação usa `standard` por padrão
- [x] Extrair os links do PDF do colega (estão em `estudo/fontes.md`)
- [ ] Causa da navegação falhando no simulador leve (ver `infra/teste-simulacao-2026-11-05.md`)
- [x] Caminho de docking do `patrol_loop` e da base falsa: rodou em 2026-11-09 (ver `progresso/`)
- [x] `Robot failed to dock` logo após `Dock succeeded`: confirmado em 2026-11-12 que era a base falsa atualizando o `/dock_status` tarde. Com a correção, o `patrol_loop` oficial chegou a `Charging...` (`progresso/testes.md`, seção 6.2)
- [ ] Lidar do Gazebo: os 640 raios voltaram todos com 0,16 m no mundo vazio. Testar com uma caixa na frente do robô (entra na medição M-GZ, no mundo `maze`)
- [ ] ~~Rodar o `patrol_loop` no Gazebo `warehouse` com Nav2~~ Despriorizado em 2026-11-09: o foco da patrulha é o simulador leve (restrições do notebook). Revisão de 2026-11-10: o `warehouse` continua fora, mas o Gazebo `maze` enxuto entra como degrau L3 da spec, se a medição M-GZ aprovar
- [ ] A navegação do simulador leve funcionou em 9/nov: repetir algumas vezes para saber se a falha de 5/nov era intermitente
- [ ] A janela do RViz abriu no treino leve? (Roberto viu?)
- [ ] Regras e limites oficiais do Kaggle: a página não abriu para leitura automática
- [ ] Limites atuais de The Construct e dos planos gratuitos de LLM

**Próximos degraus da patrulha (2026-11-13):** os passos 1 a 6 da spec estão concluídos. O que vem agora (M-GZ e L3, L4 no INF e a revisão das decisões) está em `progresso/proximos-degraus.md`.

Spec `patrol-inf` (execução iniciada em 2026-11-12, ver `docs/registro-de-mudancas.md`):
- [x] Pacote `patrulha_tb4` com a suíte L0 (124 testes, 0,3 s)
- [x] H2 decidida (base falsa)
- [x] L1: os 10 cenários aprovados em 12 e 13/nov, com o ciclo de recarga em 386 s (`progresso/testes.md`, seção 6.3)
- [x] L1b aprovado em 2026-11-13: H4 confirmada, desde que o simulador leve receba `enable_stamped_cmd_vel: true`
- [ ] Falha do Nav2 ao subir no leve ("transform from base_link to odom did not become available"), vista 2 vezes em 16 subidas (12 e 13/nov), com e sem carga no notebook. Pode ser a mesma falha intermitente de 5/nov. Causa não confirmada (hipótese: corrida com a pose inicial). O `teste_l1.sh` tenta de novo sozinho, mas isso ainda não foi exercitado
- [ ] Revisar as decisões tomadas onde a spec não dizia (tabela em `docs/registro-de-mudancas.md`), e decidir se entram no DEFINE e no DESIGN
- [ ] Como o PC fala com o robô real: **feito em 2026-11-16** (`infra/compose/robo.yaml`, com `network_mode: host` e `infra/lab/rede_lab.env`, pelo atalho `infra/docker/lab.sh robo`). Falta testar no laboratório e perguntar à equipe do INF o modo de discovery e o `ROS_DOMAIN_ID` do robô
- [ ] Modo SLAM (2026-11-16): testar no PC do laboratório, primeiro `lab.sh sim` (Gazebo) e depois `lab.sh robo`. Detalhes e o que não foi verificado: `docs/tarefas/2026-11-16-modo-slam.md` e `docs/tarefas/2026-11-16-compose-e-alvos.md`
- [ ] Construir as imagens no PC do lab (`construir_imagem.sh robo sim`) e anotar o tamanho de cada uma (`docker images physical-ai`), para confirmar que o Gazebo é a parte pesada
- [ ] Tela do TurtleBot 4 com ruído (foto `erro_tela.jpeg`, 2026-11-12): não investigado
- [ ] `git init`: recomendado no DESIGN, decisão do Roberto
- [ ] L1 com um destino abortado pelo próprio Nav2 (ponto livre, mas inalcançável): hoje só o L0 prova esse caminho

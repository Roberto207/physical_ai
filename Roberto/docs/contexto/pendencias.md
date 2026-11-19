# Pendências e dúvidas em aberto

Só o que está aberto. Os itens fechados estão no fim de `docs/historico/resultados-jazzy.md`.

## Perguntar ao coordenador

Prazo das missões: cerca de 1 mês e meio, a partir de 2026-11-05.

- [ ] **Qual é a data exata de entrega e "pronto" é em simulação ou no robô real?**
- [ ] A missão pode ser dividida na equipe (patrulha e LLM em paralelo)?
- [ ] Qual modelo de TurtleBot (padrão ou Lite) e quantos há no INF?
- [ ] Como reservar e acessar os robôs no INF? Há rede Wi-Fi dedicada?
- [ ] Qual é a plataforma do gêmeo digital (versão do Gazebo? há um repositório?) e quem a mantém?
- [ ] Qual provedor de LLM usar (a OpenAI exige chave paga)? O INF/AKCIT tem GPU ou créditos de API?
- [ ] Existe um marco ou entrega intermediária nos 10 meses?
- [ ] O notebook pode ser só cliente? O INF oferece servidor para simulação?
- [ ] Como acessar esse servidor de fora (SSH, VPN, rede do campus)? Há interface gráfica remota?

## Migração para Humble e PC do laboratório

- [ ] **Migração para Humble (spec `specs/migracao-humble/`, aprovada em 2026-11-18).** Código das fases F0 a F4 pronto e conferido no notebook (`docs/tarefas/2026-11-18-f0-preparo.md` a `docs/tarefas/2026-11-18-f4-limpeza.md`). **Falta no PC do lab:** V1 (`construir_imagem.sh base robo sim`), o teste de fumaça do Gazebo, a V3 e os 11 cenários L1, e a SEG-01 com a imagem Jazzy. **Depois, com permissão:** a V5 (robô). Até a V5, **não usar o `lab.sh robo`**
- [ ] Modo SLAM: `lab.sh sim` testado no PC do laboratório em 2026-11-16 (mapa `teste_maze`, `UTILIZÁVEL`, 17 m x 15 m). Falta o `lab.sh robo` (`docs/tarefas/2026-11-16-modo-slam.md` e `docs/tarefas/2026-11-16-compose-e-alvos.md`)
- [ ] A `physical-ai:base` é hoje um apelido da `robo` (`docker tag`). Para ter a base de verdade: `construir_imagem.sh base`

## Robô e rede

- [ ] O robô físico é Lite ou padrão? O log do robô diz `Device type: OAK-D-PRO`, a câmera do modelo padrão (o Lite usa a OAK-D Lite). Confirmar com o INF
- [ ] Robô no Wi-Fi `PixelLab-2.4GHz` (2026-11-16): confirmar que reconecta sozinho depois de reiniciar, pedir ao INF a reserva de DHCP do `192.168.7.7` e, se for preciso, descobrir por que o canal 157 (`PixelLab-5GHz`) some (`docs/guias/acesso-ao-robo.md`)
- [ ] Tela do TurtleBot 4 com ruído (foto `erro_tela.jpeg`, 2026-11-12): não investigado
- [ ] Falta com o robô: SLAM, teleop e Nav2 (a rede já chega: `lab.sh robo checar-rede` com `REDE OK`; `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md`)

## Patrulha (spec `specs/patrol-inf/`)

Próximos degraus (2026-11-13), os três dependem de pedido ou decisão do Roberto:

- [ ] **Medição M-GZ** (Gazebo `maze` sem janela, primeiro sem e depois com Nav2): mede o fator de tempo real, a RAM, a bateria, a doca, o lidar e um destino de 2 m. Só roda com pedido explícito. Plano e critérios em `specs/patrol-inf/DESIGN.md`, seção 3. Só depois dela vem o TST-08 e o degrau L3 (`workspace/meu_ws/src/patrulha_tb4/config/gazebo_maze.yaml` já existe e foi validado contra o mapa)
- [ ] **L4 (robô do INF):** o roteiro é `specs/patrol-inf/kit-de-campo.md`. Antes da visita, decidir como o PC fala com o robô (a configuração de rede está em `docs/contexto/maquinas.md`; falta testar o `lab.sh robo` na V5)
- [ ] Revisar as decisões que tomei onde a spec não dizia (tabela na entrada de 12/nov de `docs/historico/registro-de-mudancas.md`) e dizer quais entram no `DEFINE.md` e no `DESIGN.md`
- [ ] `/battery_state` do Gazebo não entregou mensagem nos testes. Causa provável: sai a cada 10 s simulados, cerca de 55 s de relógio a 0,18 do tempo real. Confirmar na M-GZ
- [ ] Lidar do Gazebo: os 640 raios voltaram todos com 0,16 m no mundo vazio. Testar com uma caixa na frente do robô (entra na M-GZ, no mundo `maze`)
- [ ] Falha do Nav2 ao subir no leve ("transform from base_link to odom did not become available"), vista 2 vezes em 16 subidas (12 e 13/nov). Causa não confirmada (hipótese: corrida com a pose inicial). O `teste_l1.sh` tenta de novo sozinho, mas isso nunca foi exercitado
- [ ] Causa da navegação falhando no simulador leve em 5/nov, que não se repetiu em 9/nov
- [ ] A janela do RViz abriu no treino leve? (o `treino_leve.sh` saiu na migração; só vale se voltar a importar)
- [ ] L1 com um destino abortado pelo próprio Nav2 (ponto livre, mas inalcançável): hoje só o L0 prova esse caminho
- [ ] Medir no robô real o tempo até o `is_docked: true` (kit de campo, etapa 3)

## Outras

- [ ] Regras e limites oficiais do Kaggle: a página não abriu para leitura automática
- [ ] Limites atuais de The Construct e dos planos gratuitos de LLM
- [ ] `git init` recomendado no DESIGN: decisão do Roberto

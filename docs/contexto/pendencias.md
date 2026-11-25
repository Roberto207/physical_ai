# Pendências e dúvidas em aberto

Atualizado em 25/11/2026. Só o que está aberto. A lista anterior (apagada no commit `97dcfc1`) pode ser lida com `git show 97dcfc1^:Roberto/docs/contexto/pendencias.md`.

## Perguntar ao coordenador

Sem resposta registrada no repositório.

- [ ] Data exata de entrega (o prazo informado em 05/11 era de cerca de um mês e meio), e se "pronto" é em simulação ou no robô real
- [ ] A missão pode ser dividida na equipe (patrulha e LLM em paralelo)?
- [ ] Modelo do TurtleBot 4 (o log diz `OAK-D-PRO`, a câmera do modelo padrão)
- [ ] Qual é a plataforma do gêmeo digital e quem a mantém?

## LLM

Plano em `specs/llm-integracao/PLANO.md`; código em `workspace/meu_ws/src/llm_tb4/`.

- [ ] Confirmar antes da execução: validação no lugar de `exec()`, e sem dock e pose `[0, 0]` automáticos na partida (é o que o código faz hoje)
- [ ] Definir o que fazer quando chega uma mensagem durante o dock ou a saída da doca
- [ ] Perguntas, condições e afirmações ainda podem virar ação (51 de 265 do avaliador, em 25/11)
- [ ] Pedidos de parar em formas novas não reconhecidos (10 de 20)
- [ ] Código de execução com o `TurtleBot4Navigator` (fase 4), com cancelamento por nova mensagem; o simulador é do operador
- [ ] Escolher como o simulador alcança o interpretador e testar o simulador leve com o `mapa_lab_novo`
- [ ] Medir o tempo de resposta com os contêineres do robô no ar
- [ ] Coordenada com vírgula decimal entre parênteses separada por ", " não é lida (recusa)
- [ ] `TEMPO_LIMITE_S` vale por operação de rede, não no total; o pedido ao Ollama obedece a `http_proxy`, se definido
- [ ] `patrol_loop.py` e `loop.py` não tratam bateria `NaN` (a comparação com o limite é falsa)

## Patrulha no robô

- [ ] Rodar no robô os três programas depois das mudanças de 25/11; `patrol_loop2.py` e `loop.py` não têm registro de ensaio físico
- [ ] Falhas do Nav2 no ponto 1 em 23/11: causa desconhecida (`docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`)
- [ ] Quedas do AMCL e do Nav2 por perda de heartbeat em 23/11: causa desconhecida
- [ ] Volta à doca falhou no único ensaio que completou os quatro pontos
- [ ] Nav2 descarta parte dos scans por atraso; comparar Wi-Fi e cabo (`docs/tarefas/2026-11-22-analise-problema-nomeado.md`)
- [ ] `rodar.sh` exige o contêiner do RViz, que consome muita CPU; decidir se continua obrigatório
- [ ] `mapa_lab_novo` tem cerca de 59,8% de área não mapeada

## Skill `preflight-robo`

- [ ] Sessão nova do `claude`: as skills aparecem ao digitar `/` (P1)
- [ ] Validar no robô: fases A e C, P2 com o robô desligado, P4 a P6 e as dúvidas da seção 8 da spec
- [ ] O C3 reprova qualquer `no map received`; em 23/11 esse aviso apareceu também enquanto o mapa ainda chegava. Ver na prática se reprova subida boa

## Robô e rede

- [ ] Reserva de DHCP para o `192.168.7.7` e reconexão do Wi-Fi após reiniciar
- [ ] Rede `PixelLab-5GHz` não aparece no robô (`docs/guias/acesso-ao-robo.md`)
- [ ] O robô usa a senha padrão do usuário `ubuntu`
- [ ] Tela do TurtleBot 4 com ruído (12/11): não investigado

## Repositório e simulação

- [ ] `test_o_modulo_de_validacao_nao_importa_ros` falha na suíte completa dentro da imagem do ROS e passa sozinho
- [ ] Teste de fumaça do Gazebo e os cenários L1 em Humble: sem registro de execução
- [ ] Medição M-GZ: só com pedido do Roberto (`specs/patrol-inf/DESIGN.md`, seção 3)
- [ ] Ramos remotos `feat_gotodock` e `v2-patrol-oficial`: decidir se integram ou saem
- [ ] A `patrulha_tb4` continua mantida ou será aposentada? (o Nav2 e a localização usam arquivos do pacote)

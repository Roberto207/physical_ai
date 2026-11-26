# Pendências e dúvidas em aberto

Atualizado em 26/11/2026. Só o que está aberto. A lista anterior (apagada no commit `97dcfc1`) pode ser lida com `git show 97dcfc1^:Roberto/docs/contexto/pendencias.md`.

## Perguntar ao coordenador

Sem resposta registrada no repositório.

- [ ] Data exata de entrega (o prazo informado em 05/11 era de cerca de um mês e meio), e se "pronto" é em simulação ou no robô real
- [ ] A missão pode ser dividida na equipe (patrulha e LLM em paralelo)?
- [ ] Modelo do TurtleBot 4 (o log diz `OAK-D-PRO`, a câmera do modelo padrão)
- [ ] Qual é a plataforma do gêmeo digital e quem a mantém?

## Reformulação de 26/11 (`specs/reformulacao-task1/SPEC.md`, seção 6)

- [ ] No PC do lab: `docker build -t physical-ai docker/`, `scripts/checar.sh`, `scripts/subir.sh` e `scripts/subir.sh nav2`
- [ ] `bond_timeout` do Nav2 em 120 com o launch oficial (`ros2 param get <ns>/lifecycle_manager_navigation bond_timeout`); se não, voltar à cópia do `navigation_launch.py` da tag
- [ ] `scripts/patrulha.sh voltas 1` e o LLM (`scripts/llm.sh`, depois `mover` com um ponto e um "pare") no robô
- [ ] `python3 llm/avaliar.py` no PC, comparado aos números de 25/11
- [ ] Cancelamento do dock e do undock pelo "pare" (código novo, sem ensaio)

## LLM

Código em `llm/`; guia em `docs/guias/llm.md`.

- [ ] Perguntas, condições e afirmações ainda podem virar ação (51 de 265 do avaliador, em 25/11)
- [ ] Pedidos de parar em formas novas não reconhecidos (10 de 20)
- [ ] Medir o tempo de resposta com os contêineres do robô no ar
- [ ] `TEMPO_LIMITE_S` vale por operação de rede, não no total; o pedido ao Ollama obedece a `http_proxy`, se definido
- [ ] `robo.py` não trata bateria `NaN` na patrulha (a comparação com o limite é falsa); o LLM recusa sair com `NaN`

## Patrulha no robô

- [ ] `patrulha.py ida-e-volta`, `continuo` e `doca` sem ensaio físico (as rotas vêm do `patrol_loop2.py` e do `loop.py`, que também não tinham)
- [ ] Falhas do Nav2 no ponto 1 em 23/11: causa desconhecida (`docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`)
- [ ] Quedas do AMCL e do Nav2 por perda de heartbeat em 23/11: causa desconhecida
- [ ] Volta à doca falhou no único ensaio que completou os quatro pontos
- [ ] Nav2 descarta parte dos scans por atraso; comparar Wi-Fi e cabo (`docs/tarefas/2026-11-22-analise-problema-nomeado.md`)
- [ ] `mapa_lab_novo` tem cerca de 59,8% de área não mapeada

## Skill `preflight-robo`

- [ ] Sessão nova do `claude`: as skills aparecem ao digitar `/` (P1)
- [ ] Validar no robô: fases A e C, P2 com o robô desligado, P4 a P6 e as dúvidas da seção 8 da spec
- [ ] O C3 reprova qualquer `no map received`; em 23/11 esse aviso apareceu também enquanto o mapa ainda chegava. Ver na prática se reprova subida boa

## Robô e rede

- [ ] Futuro: vários robôs ao mesmo tempo, com patrulha conjunta em que cada um sabe a posição dos outros
- [ ] `robot3`: a Create 3 chegou a 100% de processador com os serviços do PC no ar, e a odometria, a bateria e a doca pararam de aparecer (`docs/tarefas/2026-11-25-llm-robot3-correcoes.md`)
- [ ] O `checar-rede` aprova pela lista de tópicos; falta conferir se os dados chegam
- [ ] `robot3`: subir localização, RViz e Nav2 pelo PC
- [ ] Hipótese H1: o PC recebe os dados do robô sem as rotas 192.168.185/186 (`specs/multi-robos/BRAINSTORM.md`)
- [ ] `robot3`: medir a posição da doca e o ponto de aproximação; os da patrulha (`robo.py`) são os mesmos para todos os robôs
- [ ] `robot3`: reserva de DHCP para o `192.168.68.53`
- [ ] Reserva de DHCP para o `192.168.7.7` e reconexão do Wi-Fi após reiniciar
- [ ] Rede `PixelLab-5GHz` não aparece no robô (`docs/guias/acesso-ao-robo.md`)
- [ ] O robô usa a senha padrão do usuário `ubuntu`
- [ ] Tela do TurtleBot 4 com ruído (12/11): não investigado

## Repositório

- [ ] Ramos remotos `feat_gotodock` e `v2-patrol-oficial`: decidir se integram ou saem
- [ ] Task 2 (três robôs): fase Define a partir de `specs/multi-robos/BRAINSTORM.md`

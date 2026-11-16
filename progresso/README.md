# Progresso: o que já foi feito e testado

Última atualização: 2026-11-13.

## Resposta direta

Em 5/nov e 9/nov foi montado um ambiente ROS 2 Jazzy em Docker e testados cinco ambientes de simulação do TurtleBot 4. O `patrol_loop` oficial rodou de ponta a ponta no simulador leve: patrulhou, detectou bateria baixa, voltou à base e fez o docking. Ficaram abertos o erro `Robot failed to dock` logo após o docking e a estranheza do lidar no Gazebo.

**Primeira entrega (patrol_loop):** parcial. O ciclo de recarga ainda não fechou, e os gates de entrega ainda não estão registrados. Detalhes em `patrol-loop.md`.

**Robô do INF:** ainda não está pronto (medição de 2026-11-10 em `patrol-loop.md`). O caminho até lá está em `../specs/patrol-inf/` (BRAINSTORM, DEFINE e DESIGN, aprovados em 2026-11-10).

## Novidade de 12 e 13/nov: os passos 1 a 6 da spec `patrol-inf` estão concluídos

O nosso pacote `patrulha_tb4` existe e roda. A lógica passa em 124 testes sem ROS (0,3 s). No simulador leve, o nó fechou o ciclo de recarga em 386 s (limite de 900 s) e passou nos 11 cenários do L1, incluindo o L1b, com o `nav2.yaml` do TurtleBot 4. A hipótese H2 foi confirmada: o falso `Robot failed to dock` vinha da nossa base falsa. Números em `testes.md`, seção 6. Cada mudança, com o objetivo, em `../docs/registro-de-mudancas.md`. O roteiro para o laboratório está em `../specs/patrol-inf/kit-de-campo.md`. Próximos degraus: a medição M-GZ e o L3 (Gazebo), e o L4 (robô do INF).

## Índice

| Arquivo | O que tem |
|---|---|
| `conceitos.md` | O que é cada coisa (TurtleBot 4, Docker, Gazebo, Nav2, simulador leve, turtlesim, lidar), com exemplos |
| `testes.md` | Todos os testes, com números, o que funcionou e o que não |
| `patrol-loop.md` | O exemplo oficial de patrulha: como funciona, os três defeitos e a execução de 9/nov |
| `origem-das-pecas.md` | De onde vem cada parte do teste da patrulha (mapa, robô, bateria, doca...) e o que é real ou falso |
| `proximos-degraus.md` | O que vem depois dos passos 1 a 6 da spec `patrol-inf`: M-GZ e L3, L4 no INF e a revisão das decisões |
| `reuniao.md` | Fala sugerida, o que dizer e o que não dizer, perguntas para o coordenador |
| `evidencias/` | Log da patrulha, foto da câmera do Gazebo e o script que mede os sensores |

## Quadro geral

| Ambiente | RAM | Situação em 9/nov |
|---|---|---|
| Testes em Python puro (`pytest`) | desprezível | 19 testes passam (testado em 5/nov) |
| Suíte L0 do pacote `patrulha_tb4` (12/nov) | desprezível | 124 testes passam em 0,3 s |
| Simulador leve + **o nosso nó** `patrulha_tb4` (12/nov) | 0,4 a 0,5 GiB | Ciclo de recarga em 386 s; os 11 cenários do L1 aprovados (13/nov) |
| `turtlesim` | pequena | Topic e action funcionam (5/nov) |
| Simulador leve (`nav2_loopback_sim`) + `patrol_loop` | 0,5 a 0,7 GiB | Roda e a patrulha completa funcionou |
| Gazebo sem janela (CPU ou GPU Intel) | 1,6 a 1,9 GiB | Roda a 5% e 18% do tempo real (5/nov) |
| Gazebo com janela | 2,6 GiB (teto de 3,5) | Roda; lidar e câmera chegam |
| Gazebo `warehouse` com Nav2 | provavelmente acima de 3 GiB | **Nunca testado** |
| Robô real ou servidor do INF | | Sem acesso ainda |

## Decisão de foco (2026-11-09)

Por causa das restrições do notebook, o `patrol_loop` e a missão 1 seguem **no simulador leve**. O Gazebo fica como apoio opcional.

Revisão de 2026-11-10: na spec `../specs/patrol-inf/`, o Gazebo `maze` enxuto passou a ser o degrau L3 recomendado, porque é o único teste local com a doca, a bateria e o AMCL de verdade. Depende da medição M-GZ, ainda pendente. O leve continua o principal.

## O que ainda não foi feito

- Nav2 dentro do Gazebo (`warehouse`): despriorizado pela decisão acima. Só volta se o INF liberar servidor.
- Teste de bateria, undock e dock no Gazebo (a base de carga de lá é de verdade, não falsa): também opcional.
- Causa da falha de navegação de 5/nov: não reproduzida em 9/nov, mas também não explicada.
- Qualquer coisa no robô real ou no servidor do INF.
- A missão 2 (LLM) além da leitura do tutorial e dos exemplos em Python puro.

## Como foi gerado

Os resultados de 5/nov vêm do registro anterior (`contexto/infra/teste-simulacao-2026-11-05.md`). Os de 9/nov foram observados diretamente na sessão de 9/nov, e as saídas estão em `evidencias/`. Onde há hipótese, está marcado como hipótese.

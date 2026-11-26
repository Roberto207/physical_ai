# Patrulha pelo exemplo oficial Humble, no TurtleBot 4 Standard

Programas adaptados do [`patrol_loop.py` oficial](https://github.com/turtlebot/turtlebot4_tutorials/blob/humble/turtlebot4_python_tutorials/turtlebot4_python_tutorials/patrol_loop.py) (ramo `humble`, licença Apache-2.0) para o `mapa_lab_novo`. O robô é escolhido pela variável `ROBO` (padrão `robot1`; `docs/guias/acesso-ao-robo.md`). Usam o `TurtleBot4Navigator` ([manual](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html)).

## Arquivos

| Arquivo | Rota | Termina | Pede `SIM` |
|---|---|---|---|
| `patrol_loop2.py` | 1 → 2 → 3 → 4 → 3 → 2 → 1 | Na doca | Não |
| `loop.py` | 1, depois 3 → 4 → 3 → 1 sem fim | `Ctrl+C`, bateria baixa (volta à doca) ou falha | Não |
| `patrol_loop.py` | 1 → 2 → 3 → 4, repetido N vezes | Na doca (`0` = sem fim) | Só pelo `rodar.sh` |
| `rodar.sh` | Confere mapa, rede e contêineres e chama o `patrol_loop.py` | | Sim |

- O `patrol_loop.py` é também a **base** dos outros dois: o `patrol_loop2.py` importa dele os pontos e as funções, e o `loop.py` importa os pontos e os limites. Não apagar.
- O exemplo oficial, sem alterações, está no histórico: `git show 2578ee0:workspace/patrulha_oficial/upstream/patrol_loop.py`.
- Opção digitada errado encerra o programa com erro, sem mover o robô.

## Como rodar

Sequência completa, da subida dos serviços ao encerramento:

- `docs/guias/patrulha-volta-a-doca.md`
- `docs/guias/patrulha-loop-continuo.md`

## Pontos em uso no código

Metros, referencial `map`, no `workspace/mapas/mapa_lab_novo.yaml`. Fonte: `workspace/mapas/pontos_mapa_lab_novo.md` (os graus anotados lá não são usados; a orientação vem da direção do ponto seguinte).

| Ponto | x | y |
|---|---|---|
| Doca | -0.203 | 0.100 |
| 1 (também é a aproximação da doca) | -0.586 | -0.807 |
| 2 | -3.550 | -3.063 |
| 3 | -5.608 | -0.823 |
| 4 | -1.967 | 1.030 |

Para mudar um ponto, editar `PONTOS` somente em `patrol_loop.py`.

## Comportamento comum

- Exigem o robô na doca no início, `map→odom` recente (2D Pose Estimate no RViz; os programas não publicam a pose) e bateria a partir de 20%.
- Um destino que falha, é recusado ou passa de 120 s encerra o programa, com o robô onde está.
- O limite de 120 s não cobre um servidor de ação que não responda, nem as rotinas de dock e undock.
- `Ctrl+C` cancela a meta, sem voltar à doca. Para voltar: `patrol_loop2.py --voltar-doca`.

## Estado dos ensaios

O `patrol_loop.py` completou os quatro pontos uma vez no robô, com falha na volta à doca. Em 23/11 houve falhas no ponto 1, sem causa determinada. Não há registro de ensaio físico do `patrol_loop2.py` nem do `loop.py`. Histórico em `docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`.

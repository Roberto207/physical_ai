# BRAINSTORM: patrulha no TurtleBot 4 do INF

**Status:** Aprovado em 2026-11-10 (portão da skill `/sdd`). Revisado em 2026-11-10, a pedido do Roberto: H1, H5 e H6, riscos do Gazebo e a seção "Simuladores avaliados".
**Data:** 2026-11-10
**Trilha:** pipeline completo (BRAINSTORM → DEFINE → DESIGN)

## Resposta direta

Queremos que o TurtleBot 4 real do INF patrulhe o laboratório, volte à doca com bateria baixa, carregue e retome. Hoje, nada do nosso código está pronto para isso (medição em `docs/historico/resultados-jazzy.md`, seção "Pronto para o robô do INF?"). A ideia central desta spec é **fazer daqui tudo o que não depende do robô**, de forma que no INF só falte:

1. fazer o mapa (SLAM);
2. marcar os pontos num arquivo YAML;
3. rodar uma sequência curta de testes já escrita.

## A cena do dia a dia

É como **preparar uma mudança de casa**. Dá para embalar, etiquetar as caixas e montar a lista do que vai em cada cômodo antes de ver a casa nova. Mas a planta da casa nova, onde vai cada móvel e se a porta passa a geladeira só se descobrem lá. Se a lista estiver organizada por cômodo, a mudança no dia é rápida.

## O problema

| Hoje | Por que impede |
|---|---|
| O `patrol_loop` oficial tem os pontos do `warehouse` fixos no código (`patrol_loop.py`, linhas 92 a 95) | O laboratório é outro lugar |
| Pose inicial `(0, 0)` e aproximação da doca `(-1, 1)` fixas (linhas 81 e 111) | Só serve se o mapa tiver a doca na origem |
| Três defeitos (bateria sem valor inicial, bateria só lida entre destinos, falhas ignoradas) | No robô real, viram parada no corredor ou repetição infinita |
| `isDockComplete()` devolve `True` mesmo quando o dock falha (`turtlebot4_navigator.py`) | Uma falha de dock passa despercebida |
| Tudo o que testamos usa bateria, doca e AMCL falsos e localização perfeita | O leve não mostra o robô perdido, nem uma doca que falha de verdade |
| `workspace/meu_ws/src/` vazio | Não existe pacote nosso para levar |

## Hipóteses (a confirmar)

1. **H1:** com os pontos e a pose num YAML, o mesmo código roda no leve, no Gazebo e no robô sem mudança. Só trocam o arquivo e os argumentos de launch. O motivo: o código só fala com interfaces (`/battery_state`, `/dock_status`, as ações `/dock`, `/undock` e `navigate_to_pose`). Quem responde do outro lado muda de ambiente para ambiente (tabela na seção 1.1 do `DESIGN.md`).
2. **H2:** o falso `Robot failed to dock` vem da base falsa, que publica `/dock_status` a cada 1 s. O `getDockedStatus()` lê o último valor guardado (`turtlebot4_navigator.py`, linha 162). Na doca real da Create 3, o erro talvez não exista.
3. **H3:** fazer o mapa do laboratório com o SLAM **começando com o robô na doca** deixa a doca perto da origem do mapa. Isso simplifica a pose inicial.
4. **H4:** os parâmetros do Nav2 do TurtleBot 4 (`turtlebot4_navigation/config/nav2.yaml`) funcionam também no leve (`params_file:=`). Assim, o leve fica mais parecido com o robô real.
5. **H5:** a bateria real cai devagar (horas). Para testar a volta à doca no INF sem esperar, basta usar temporariamente limites de bateria perto da carga atual. Vale também para o Gazebo: a bateria da Create 3 simulada cai 0,0089% por segundo andando (taxa fixa no código, `robot_state.cpp` do `create3_sim`). De 100% a 20%, são cerca de 2,5 h simuladas, ou cerca de 14 h de relógio. Vira o modo `relativo` (PAT-21).
6. **H6:** o `/battery_state` "não chegou" no Gazebo porque sai **a cada 10 s simulados** (`battery_state_publish_rate: 0.1`, `robot_state_params.yaml`). A 0,18 do tempo real, isso dá cerca de 1 mensagem a cada 55 s de relógio, e os testes antigos provavelmente desistiram antes. Confirma-se na medição M-GZ (`DESIGN.md`, seção 3).

## Riscos

| Risco | Probabilidade | Impacto | Onde é tratado |
|---|---|---|---|
| A rede do INF não deixa o PC e o robô se enxergarem (outro `ROS_DOMAIN_ID`, middleware diferente ou discovery bloqueado) | Média | Alto: nada funciona pelo PC | Checklist de rede no kit de campo (DESIGN) |
| O modelo é o Lite, não o Standard | Desconhecida | Baixo para a patrulha (muda o URDF e a câmera) | Parâmetro de modelo (DESIGN) |
| O AMCL se perde no laboratório (corredores parecidos, pessoas andando) | Média | Alto | Só se testa no INF (L4). O leve nunca erra a posição |
| A doca real falha ou exige alinhamento | Média | Alto | Novas tentativas, reaproximação e espera do `is_docked` (DEFINE PAT) |
| O Wi-Fi cai durante a patrulha (se rodar no PC) | Média | Alto: o robô fica sem comando novo | Decisão aberta: PC ou Raspberry Pi |
| Pessoas e obstáculos móveis no laboratório | Alta | Segurança | Velocidade baixa nos primeiros testes, alguém ao lado, área livre |
| No Gazebo, o lidar voltou com os 640 raios em 0,16 m e o `/battery_state` não chegou | Já observado. A bateria tem causa provável (H6) | O lidar bloqueia o AMCL no Gazebo | Medição M-GZ (DESIGN, seção 3) |
| No Gazebo abaixo de cerca de 0,4 do tempo real, o Nav2 pode estourar tempos-limite (guia não oficial, [RAS](https://ras-mobile-robotics.github.io/tutorials/vm)). Estamos em 0,18 | Desconhecida | O L3 falha por lentidão, e não por erro nosso | Medição M-GZ, etapa E2 |
| O notebook trava num teste pesado | Média | Perda de trabalho | Teto de memória sempre, e o "modo enxuto" (DESIGN) |
| A definição de "pronto" (simulação ou robô) é desconhecida | Certa | Muda o critério de aceite | Pergunta ao coordenador |

## As ideias de teste local do Roberto: o que as sustenta e o que falta validar

### Ideia 1: fechar o máximo de programas e subir o container com mais RAM

| Já sustentado | Falta validar |
|---|---|
| Em 9/nov, com o Opera fechado, havia cerca de 4,5 a 5 GiB livres. O Gazebo com janela usou 2,6 GiB com teto de 3,5 GiB, sem OOM (`docs/historico/resultados-jazzy.md`) | O Gazebo **com Nav2 e localização** nunca foi medido. O valor provável passa de 3 GiB, mas é estimativa |
| O teto com `--memory` e `--memory-swap` iguais já protegeu o notebook (só o container morre) | Se 3,5 GiB bastam, e se o notebook fica usável. Com a regra de folga (teto mais 1 GiB) e 4,5 a 5 GiB livres, o teto possível é de 3,5 a 4 GiB, e não de 4,5 |
| Mais RAM evita a morte do container, mas **não acelera** o Gazebo: a lentidão é de CPU e GPU | Quanto tirar a câmera OAK-D ajuda (hipótese) |

Proposta: um "modo enxuto" que só sobe o teste se a memória livre (`free`) for **pelo menos o teto mais 1 GiB**. Sem a janela do Gazebo, sem RViz, e com o pico de RAM gravado como evidência.

### Ideia 2: patrulhar um espaço de pontos bem menor

| Já sustentado | Falta validar |
|---|---|
| O tempo cresce com a distância. No leve, o trecho `(-5, 1)` a `(-5, -23)` (24 m) levou 222 s, cerca de 0,11 m/s efetivos (`docs/historico/resultados-jazzy.md`, seção 3) | Quanto tempo leva um ciclo inteiro com pontos a 1,5 a 3 m |
| No Gazebo, a 0,18 do tempo real, 2 m levariam entre cerca de 45 s (a 0,26 m/s) e 100 s (a 0,11 m/s efetivos) de relógio | Estimativa: medir |
| Os mapas `depot` e `maze` e os mundos `depot.sdf` e `maze.sdf` já estão na imagem | Escolher uma região pequena e livre e conferir os pontos contra o mapa |

Estimativa no leve: pontos a 2 m levam cerca de 20 s cada. Com a descarga acelerada da base falsa, um ciclo inteiro (sair, 2 ou 3 pontos, voltar, carregar e sair de novo) deve caber em poucos minutos. **A medir.**

### Ideias extras

1. **Máquina de estados em Python puro**, com um navegador falso: testa em segundos casos difíceis de provocar no simulador (bateria cai no meio do trecho, dock falha duas vezes, destino inalcançável). Segue a decisão de 2026-11-05 (`docs/decisoes/README.md`).
2. **Injeção de falhas pela base falsa**: dock que falha N vezes e queda de bateria num instante escolhido. Assim o leve exercita os caminhos de erro.
3. **Limites de bateria temporários no robô real** (H5): provocam a volta à doca em minutos.
4. **Validar os pontos contra o mapa antes de andar**: pega um erro de digitação no YAML antes de o robô ir para uma parede.
5. **Gravar um rosbag** de cada teste no INF, para analisar depois em casa sem o robô.

## Simuladores avaliados (pesquisa de 2026-11-10, nada testado aqui)

| Simulador | Para Jazzy? | Realismo para a patrulha | Doca e bateria da iRobot? | Veredito |
|---|---|---|---|---|
| Leve (`nav2_loopback_sim`, atual) | Sim | Baixo: posição perfeita, lidar calculado sobre o mapa | Não, usa a base falsa | L1: a lógica e as falhas |
| Gazebo, `maze` enxuto | Sim, já na imagem | Alto: física, sensores e AMCL real | **Sim** (nós da Create 3 simulada e a doca `standard_dock`) | **L3 recomendado**, se a medição M-GZ aprovar |
| [MVSim](https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/MVSim/Simulation-MVSim.html) | Sim, `ros-jazzy-mvsim` por apt | Médio: física 2D (Box2D), tração diferencial, lidar, e mundo a partir de um mapa em imagem | Não | L3-alt (plano B). Sem exemplo pronto com Nav2, traz um TurtleBot 3, e exige mudar a imagem Docker |
| [Flatland](https://flatland-simulator.readthedocs.io/en/latest/overview.html) | Não confirmado | Médio, 2D | Não | Descartado por enquanto |
| Stage | Não achei pacote | Médio, 2D | Não | Descartado |
| Isaac Sim | | Muito alto | | Exige GPU NVIDIA: impossível no notebook |

## Fora de escopo desta spec

- A missão 2 (LLM).
- Alterar pacotes oficiais (`turtlebot4_python_tutorials`, `turtlebot4_navigation`).
- Rodar o Nav2 no Gazebo `warehouse` completo (despriorizado em 2026-11-09). O L3 usa o `maze`, menor, com pontos curtos.
- Montar o robô no MVSim, a não ser que o L3 se mostre inviável e não haja servidor no INF.
- Implementar o código: esta spec descreve; implementar é um pedido seguinte.

## Efeito prático

Se a spec for seguida, a ida ao INF vira **uma sessão de "preencher e testar"**, não de programar. O que mais importa levar pronto: o pacote com os pontos num YAML, a validação de pontos, a checagem honesta do dock e o kit de campo.

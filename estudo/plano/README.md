# Plano de 6 semanas: patrol control e LLM no TurtleBot 4

## Resposta direta

Em 1 mês e meio dá para entregar as duas missões, **desde que o plano seja só sobre elas**. O mapa anterior de 40 semanas não cabe apertado: as fases até a LLM somavam 240 horas, e 6 semanas a 8 horas dão 48. O que tornou o corte possível é que as duas missões já têm exemplo oficial pronto: não vamos inventar a navegação, vamos usar a existente e escrever a lógica por cima.

As horas por semana e o tamanho das tarefas são estimativas minhas. Corrija ao longo do caminho.

## O projeto em uma cena

Imagine um **vigia noturno** de um galpão:

| Peça | Na cena | Na vida real |
|---|---|---|
| Patrol control | O vigia faz a ronda pelos corredores e, quando está cansado, volta para descansar e depois retoma | O robô percorre pontos em loop e volta à base quando a bateria fica baixa |
| LLM | O gerente fala por rádio "dá uma olhada no corredor B" | Uma frase em português vira um comando |
| Validador | A portaria confere se o corredor B existe e se o vigia tem condições de ir | Nosso código recusa o que for inválido ou perigoso |
| Nav2 | O vigia já sabe andar sem bater em nada; ninguém ensina isso a ele | Pacote pronto que calcula a rota e desvia de obstáculos |
| ROS 2 | O rádio pelo qual todos se comunicam | Sistema de mensagens entre os programas do robô |

Sua função é a lógica da ronda e a portaria. O "andar" já vem pronto. Por isso o plano prioriza **ler e usar** o Nav2, não entender a matemática dele.

## As 6 semanas

Datas contadas a partir de 5/nov/2026. **Confirme a data exata de entrega.**

| Semana | Datas | Tema | No fim, você consegue | Arquivo |
|---|---|---|---|---|
| 1 | 5 a 11/nov | ROS 2 na mão, sem código | Investigar um sistema ROS só pelo terminal | `semana-1-ros2-na-mao.md` |
| 2 | 12 a 18/nov | ROS 2 em Python | Escrever um programa que manda uma tarefa e acompanha o progresso | `semana-2-ros2-python.md` |
| 3 | 19 a 25/nov | Nav2 e o `patrol_loop` | Explicar linha a linha o exemplo oficial, rodando | `semana-3-nav2-e-patrol.md` |
| 4 | 26/nov a 2/dez | **Missão 1: nossa patrulha** | Patrulha testada, que reage à bateria durante o trajeto | `semana-4-missao-patrol.md` |
| 5 | 3 a 9/dez | **Missão 2: LLM** | Frase em português vira ação validada e medida | `semana-5-missao-llm.md` |
| 6 | 10 a 16/dez | Integração e demonstração | Demonstração no ambiente do INF e relatório | `semana-6-integracao.md` |
| Folga | 17 a 20/dez | Atrasos | Não conte com ela | |

Apoio: `praticar.md` (onde e como rodar), `fontes.md` (todos os links, com o que foi verificado) e `recomendado/00-glossario.md` (termos).

## O que foi cortado (e volta depois)

| Saiu por enquanto | Por quê | Risco de cortar |
|---|---|---|
| URDF, TF a fundo, QoS a fundo | As missões usam, mas não escrevem isso | Baixo. Só é preciso reconhecer os nomes |
| Criar mapas (SLAM) | Os mapas prontos servem para simulação | Alto no robô real: lá é obrigatório, com o mapa do local |
| Ajuste fino do Nav2 | Usamos os padrões | Médio, ver problema em aberto em `praticar.md` |
| Pesquisa, artigos, outros robôs | Vêm depois da entrega | Nenhum no prazo |

O mapa antigo está em `recomendado/` e vale para o restante dos 10 meses.

## Três coisas que podem derrubar o prazo

1. **"Pronto" significa o quê?** Em simulação ou no robô real? Muda a semana 6 inteira. Pergunte ao coordenador esta semana.
2. **Acesso ao INF.** Sem servidor com simulação boa, a validação final fica presa no seu notebook, que roda o Gazebo a cerca de 18% da velocidade real. Sem robô, nada real é validado.
3. **48 horas não têm sobra.** Dividir com a equipe é a maior folga disponível: as semanas 4 e 5 podem correr em paralelo com duas pessoas.

## Efeito prático

Se sobrar pouco tempo, a ordem de sacrifício é: primeiro o robô real, depois a comparação de LLMs. Patrulha e validador rodando e testados em simulação são o mínimo demonstrável. Combine isso com o coordenador antes, não na véspera.

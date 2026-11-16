# Semana 6: integração e demonstração (8 horas)

## O que é esta semana

Juntar as duas missões, validar fora do notebook e mostrar. Esta semana **depende da resposta do coordenador** sobre o que significa "pronto".

## Os dois cenários

| | Só simulação | Robô real |
|---|---|---|
| Onde | Gazebo no servidor do INF | TurtleBot 4 no INF |
| O que muda | Os mesmos pacotes, sem a base falsa | Mapa real, rede, segurança física |
| Risco | Baixo, se o acesso existir | **Alto** para 8 horas |
| Sem acesso ao INF | Vídeo do treino leve e testes, deixando claro o que não foi validado | Não dá |

## Juntar as missões

Decidir uma regra simples: a patrulha roda e, ao chegar um comando pela LLM, ela pausa, executa e retoma. Comece pelo mais simples, com um único nó que lê `user_input` e usa a mesma função `decidir`. Se o tempo acabar, entregue separadas: duas coisas que funcionam valem mais do que uma integração quebrada.

## Se for no servidor do INF

Primeiro, leia a página de [requisitos da simulação](https://turtlebot.github.io/turtlebot4-user-manual/software/simulation.html). Comando do manual:

```bash
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py nav2:=true slam:=false localization:=true rviz:=true
```

Pontos a conferir nessa ordem, pois nunca rodei isto com Nav2:

1. O robô localiza e chega a um destino simples?
2. `/battery_state` publica? Descarrega?
3. `dock` e `undock` funcionam?
4. A sua patrulha completa uma volta?
5. O comando pela LLM funciona?

## Se for no robô real

O manual diz que rodar os exemplos no robô real exige compilar do código-fonte e que isso é recomendado "para usuários intermediários ou acima". Vá acompanhado de alguém do INF.

| Ordem | O que fazer | Fonte |
|---|---|---|
| 1 | Ligar, conectar à rede | [Basic Setup](https://turtlebot.github.io/turtlebot4-user-manual/setup/basic.html), [Simple Discovery](https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html), [vídeo](https://www.youtube.com/watch?v=TPXzNKgafJg) |
| 2 | Mapear o local | [Criar mapa](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/generate_map.html) |
| 3 | Navegar até um ponto | [Navegação](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html) |
| 4 | Trocar os pontos do YAML pelos do local real | Seu pacote |
| 5 | Patrulha, depois LLM | Seu pacote |

Segurança: área livre, alguém ao lado e o robô nunca sozinho. Ao testar a LLM, comece com o validador recusando tudo que não for um local próximo.

Duas diferenças clássicas: `use_sim_time` deve ser `false` no robô, e simulação e robô não devem compartilhar a mesma rede ROS, como avisa o manual.

## O relatório (2 horas)

Curto, e já é matéria-prima para a pesquisa do projeto:

| Seção | Conteúdo |
|---|---|
| O que foi feito | Duas missões, em um parágrafo cada |
| Como rodar | Comandos |
| Resultados | Taxa de acerto, latência, voltas completas |
| O que não funcionou | Com a causa, quando conhecida. Incluir o simulador leve e o `apt` que não existe |
| O que não foi validado | Por exemplo: "docking só com base falsa" |

## Pronto quando

Alguém que não seja você roda a demonstração pelo README, e o relatório diz com clareza o que foi validado e onde.

## Depois da entrega

Volte a `recomendado/`: o mapa dos meses seguintes já está lá, incluindo SLAM, robô real a fundo e pesquisa.

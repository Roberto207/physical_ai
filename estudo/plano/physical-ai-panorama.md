# Panorama de Physical AI: além do TurtleBot

O projeto vai trabalhar com robôs humanoides, quadrúpedes e com rodas. O TurtleBot é a porta de entrada. Esta é uma lista de áreas para ir lendo em paralelo, **sem cobrar profundidade** nos primeiros meses.

Todos os itens abaixo são direções a verificar com leitura; não os tomo como estabelecidos.

| Área | O que é | Quando olhar |
|---|---|---|
| Navegação autônoma (Nav2) | Mapa, localização e planejamento. É o que fazemos no TurtleBot | Fases 3 a 4 |
| LLM como planejador | Linguagem natural vira ação por tool calling | Fase 5 |
| Modelos visão-linguagem-ação (VLA) | Um único modelo vê a imagem e a instrução e gera ações do robô (por exemplo RT-2, OpenVLA, famílias π) | A partir da fase 5, só leitura |
| Aprendizado por imitação | O robô aprende a partir de demonstrações humanas (por exemplo a biblioteca LeRobot, da Hugging Face) | Fase 7 |
| Aprendizado por reforço em simulação | Treinar políticas em milhares de simuladores paralelos, comum em quadrúpedes e humanoides | Fase 7, leitura |
| Manipulação | Braços e garras, e pegar objetos | Se o projeto trouxer braços |
| Locomoção com pernas | Quadrúpedes e humanoides, normalmente controlados por políticas de RL | Quando chegarem os robôs |
| Gêmeos digitais | Cópia virtual sincronizada com o real. Gazebo (INF), e outros como Isaac Sim ou MuJoCo | Ao longo de todo o projeto |
| Sim2real | Diferença entre o simulado e o real: física, sensores, atraso | Fases 6 e 7 |

## Como ler sem se perder

Uma ficha por artigo ou projeto, em `../pesquisas/`:

- Problema que resolve
- Robô e simulador usados
- **O que funcionou e com que métrica**
- **O que não funcionou ou ficou fora**
- Dá para reproduzir na nossa estrutura? Por quê?

Esse formato alimenta direto a fase 7 e a pergunta do projeto sobre o que funciona e o que não funciona.

## Limite de hardware

Sem GPU NVIDIA no notebook, treino de RL e VLA pesado não roda localmente. Com o notebook cliente, isso depende de GPU no INF ou na AKCIT. Perguntar ao coordenador.

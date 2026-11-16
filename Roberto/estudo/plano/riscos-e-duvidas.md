# Riscos e dúvidas do plano

## Premissas que precisam de confirmação

| Premissa | Se for falsa |
|---|---|
| O notebook será só cliente e o INF fornece simulação | Voltamos a rodar tudo local (cerca de 18% do tempo real no melhor caso, sem Nav2, ver teste). Pode servir para estudar, não para avaliar |
| O INF permite acesso remoto (SSH ou VPN) | A fase 2 vira "ir fisicamente ao INF" |
| O robô físico do INF é TurtleBot 4 (padrão ou Lite) | Alguns capítulos do manual mudam (sensores) |
| Jazzy e Ubuntu 24.04 são o padrão da equipe | Trocar de versão muda pacotes e tutoriais |
| A equipe tem acesso a uma LLM (API ou GPU) | Missão 2 fica limitada a modelos pequenos |

## Riscos técnicos

| Risco | Probabilidade | O que fazer |
|---|---|---|
| Tutoriais do Humble não funcionam no Jazzy | **Já confirmado** para o apt de `turtlebot4_tutorials` | Compilar do GitHub e documentar |
| Multicast bloqueado na rede do campus | Média | Discovery Server ou alternativa (fase 2) |
| Docking instável em simulação | Média | Testar no robô real, registrar como limitação |
| Custo da API de LLM | Média | Definir teto de gasto e alternativa aberta |
| Segurança do robô com LLM | Alta importância | Validação, ações discretas e acompanhamento humano |

## Riscos de pessoas e tempo

- 8 horas por semana é pouco. Se perder duas semanas, a fase correspondente escorrega e as seguintes também. Por isso cada fase tem entregável: se não saiu, é sinal para ajustar o plano, não para acumular atraso.
- Dependência do INF: acesso ao robô e ao servidor pode atrasar. Ter sempre um trabalho local útil (leitura, código em `turtlesim`) para os períodos de espera.
- Diferença de nível na equipe: dividir tópicos e fazer apresentações curtas de 15 minutos entre os membros.

## Ajustes sugeridos ao plano

1. Pedir o acesso ao INF **agora**, pois a fase 2 depende dele e é a mais incerta.
2. Marcar a visita ao robô na semana 2.
3. Revisar este mapa a cada 4 semanas.

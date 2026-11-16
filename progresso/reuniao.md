# Reunião: o que dizer

## Resposta direta

Você tem uma semana de trabalho concreto: ambiente reproduzível, cinco simulações testadas, limites da máquina medidos e a patrulha oficial rodando com um defeito demonstrado. O que falta depende do INF.

## Fala sugerida (cerca de 1 minuto)

Essa semana estudei ROS 2 e montei um ambiente de teste em Docker com Ubuntu 24.04 e ROS 2 Jazzy, que já inclui o simulador do TurtleBot 4. Usei o turtlesim, um simulador 2D simples, para praticar nodes, topics e actions. Depois testei o Gazebo, que simula a física e os sensores do robô, e um simulador leve com o Nav2, que é o pacote de navegação do robô. Descobri que meu notebook não aguenta bem o Gazebo: ele roda a cerca de 18% da velocidade real no melhor caso, e com janela precisa de mais de 2,5 GiB de memória. O simulador leve rodou bem melhor, com cerca de 0,5 GiB, e foi nele que li e testei o `patrol_loop`, o exemplo oficial de patrulha. Ele patrulhou três pontos, voltou à base quando a bateria ficou baixa e fez o docking, e deu para ver um defeito do código ao vivo: ele só olha a bateria entre destinos. Para avançar, preciso saber se posso simular em um servidor do INF e se "pronto" significa em simulação ou no robô real.

## Dizer com cuidado

| Afirmação | Por quê |
|---|---|
| "A base e a bateria são simuladas por mim" | O simulador leve não tem base nem bateria de verdade |
| "Nada foi testado no robô real" | Verdade, e evita a pergunta |
| "A navegação funcionou desta vez" | Falhou em 5/nov, a causa não foi achada |
| Não diga "o Nav2 rodou no Gazebo" | Nunca foi testado lá |
| Não cite RTF do simulador leve | Não foi medido |

## Perguntas para o coordenador

1. Qual é a data exata de entrega e "pronto" é em simulação ou no robô real?
2. O INF tem servidor para simulação, e como acessar de fora (SSH, VPN)?
3. Qual modelo de TurtleBot 4 (Standard ou Lite) e como reservar um?
4. Qual versão do ROS a equipe vai padronizar?
5. A missão pode ser dividida (patrulha e LLM em paralelo)?
6. Qual provedor de LLM, com chave ou créditos?

## Perguntas que podem fazer a você

| Pergunta | Resposta curta |
|---|---|
| Por que Docker? | O notebook é Debian e o Jazzy pede Ubuntu 24.04. O container traz o Ubuntu junto |
| Por que não simula tudo no notebook? | Gazebo a 18% do tempo real no melhor caso, e com janela pede 2,6 GiB ou mais |
| O que o `patrol_loop` faz? | Patrulha pontos e volta à base para carregar quando a bateria fica baixa |
| Quais os defeitos dele? | Bateria sem valor inicial, bateria só vista entre destinos e resultado do destino ignorado |
| O que vai melhorar primeiro? | Olhar a bateria durante o trajeto |
| O docking funciona? | A action respondeu sucesso no simulador leve, mas o programa logou falha, provavelmente por causa da base falsa. Não confirmado |

## Próximos passos para propor

- Semana 4: patrulha própria que reage à bateria durante o trajeto, e resolver o falso erro de dock.
- Foco da patrulha: o simulador leve, por causa das restrições do notebook. O Gazebo só entra se o INF liberar servidor.
- Semana 5: LLM com ações validadas e medição com frases em português.
- Semana 6: integração e demonstração.

# AGENTES.md — regras para agentes de IA neste projeto

Este arquivo reúne as regras que o Roberto já definiu para o Claude Code na máquina dele e que agentes de IA em outra máquina também precisam seguir. Leia inteiro antes de agir. Se uma regra aqui conflitar com um pedido, pare e pergunte ao Roberto.

Origem: memória do Claude Code do Roberto, copiada em 2026-11-16. Se a memória mudar, este arquivo pode ficar desatualizado.

## 1. Guardrails do TurtleBot 4 físico (obrigatórios)

Desde 2026-11-12 os testes são feitos nos robôs reais (TurtleBot 4). Erro em hardware real não se desfaz com reset: o robô pode se danificar, causar acidente ou ficar desconfigurado.

Regras:

- Siga sempre a documentação oficial do TurtleBot 4 (Clearpath) e de qualquer ferramenta usada: ROS 2, Nav2, Create 3 etc.
- Peça permissão explícita ao Roberto antes de qualquer ação crítica, fora das especificações ou que não esteja na documentação oficial.
- Sem permissão, não faça nada disto: enviar comandos que movam o robô; alterar firmware, configuração ou rede do robô; rodar no robô qualquer coisa não documentada.

Como aplicar:

- Antes de qualquer comando que toque o robô físico, cite a página da documentação oficial que o embasa.
- Se não houver documentação, ou se a ação for crítica, pare e peça autorização. São críticos: movimento, velocidades altas, docking e undocking, atualização de firmware, mudança de rede ou DDS, apagar dados.
- Valide no simulador antes de ir ao robô (ver seção 3).

## 2. Projeto e prazo

- Roberto é bolsista no projeto AKCIT de Physical AI (INF-UFG, cerca de 10 meses).
- Entrega da equipe: patrol control e integração de LLM no TurtleBot 4.
- Prazo informado: cerca de 1 mês e meio a partir de 2026-11-05, ou seja, por volta de 20/dez/2026. A data exata não foi confirmada.
- Carga: cerca de 8 horas por semana.
- Priorize o que serve a essas duas missões e deixe o resto para depois.
- Pendência em aberto: "pronto" significa em simulação ou no robô real? Não assuma.

## 3. Simulador: o leve é o principal

Decisão de 2026-11-09, revista em 2026-11-10:

- O foco do `patrol_loop` é o simulador leve (degrau L1). Ele só testa a lógica: bateria, doca e AMCL são falsos.
- O Gazebo `maze` enxuto é o degrau L3 recomendado na spec `specs/patrol-inf/`: sem janela, sem RViz, teto de 3,5 GiB de memória, pontos curtos, limites de bateria relativos, base falsa desligada. Ele traz a Create 3 simulada (bateria e doca da iRobot) e um AMCL real, mas roda a cerca de 0,18 do tempo real.
- O Gazebo `warehouse` com Nav2 continua fora.
- Não rode a medição M-GZ (plano no DESIGN, seção 3) sem pedido explícito do Roberto.

## 4. Limite de memória (máquina do Roberto)

O notebook do Roberto tem 7,4 GiB de RAM e GPU Intel integrada. Ele já travou durante um `docker build` sem limite.

- Nunca rode `docker build` nem processos pesados sem limite de memória.
- Use `docker run --memory=X --memory-swap=X`. Para instalar pacotes, use `docker commit` em vez de `docker build`.
- Acompanhe a RAM livre e pare o container se ela cair demais.
- Avise antes de abrir janelas gráficas e testes longos.
- Scripts seguros ficam em `infra/docker/`.
- Em outra máquina, confira primeiro quanta RAM há e ajuste o teto. Na dúvida, use o limite acima.

## 5. Como explicar e planejar para o Roberto

Ele é iniciante em robótica. Um plano com termos soltos e sem links já foi criticado.

- Para cada etapa, explique o que é e por quê, com uma analogia do dia a dia.
- Dê o link exato e a ordem de leitura.
- Dê comandos testados para praticar e o critério de "pronto".
- Diga o que foi e o que não foi verificado em cada fonte.
- Defina todo termo técnico na primeira vez que usar.

## 6. Onde achar o resto

Os caminhos abaixo são relativos a `Roberto/contexto/`.

| O que | Arquivo |
|---|---|
| Escopo e missões | `projeto/escopo.md`, `projeto/missoes-iniciais.md` |
| Decisões já tomadas | `projeto/decisoes.md` |
| Briefing original | `projeto/briefing-original.md` |
| Pendências | `pendencias.md` |
| Máquina do Roberto | `infra/maquina-roberto.md` |
| Fontes e stack | `tecnologias/fontes-e-stack.md` |

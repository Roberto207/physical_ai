# AGENTES.md — regras para agentes de IA neste projeto

Este arquivo reúne as regras que o Roberto já definiu para o Claude Code na máquina dele e que agentes de IA em outra máquina também precisam seguir. Leia inteiro antes de agir. Se uma regra aqui conflitar com um pedido, pare e pergunte ao Roberto.

Origem: memória do Claude Code do Roberto, copiada em 2026-11-16 e revisada em 2026-11-18 (enxugamento, `docs/historico/spec-enxugamento.md`). Se a memória mudar, este arquivo pode ficar desatualizado.

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
- Entrega da equipe: patrol control e integração de LLM no TurtleBot 4. Detalhes em `docs/contexto/projeto.md`.
- Prazo informado: cerca de 1 mês e meio a partir de 2026-11-05, ou seja, por volta de 20/dez/2026. A data exata não foi confirmada.
- Carga: cerca de 8 horas por semana.
- Priorize o que serve a essas duas missões e deixe o resto para depois.
- Pendência em aberto: "pronto" significa em simulação ou no robô real? Não assuma.

## 3. Simulador e distro (ADR-001 e ADR-002)

- Todas as imagens são **ROS 2 Humble** (`docs/decisoes/ADR-001-ros2-humble.md`). O Jazzy fica só na tag git `jazzy-final`.
- O simulador principal é o **Gazebo Fortress sem janela no PC do laboratório** (`docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md`). O pacote `lab_tb4` o configura.
- O `nav2_loopback_sim` (vendorizado) continua como **L1**: injeção de falhas e teste da lógica do nó. Bateria, doca e AMCL dele são falsos.
- O Gazebo `warehouse` com Nav2 continua fora.
- Não rode a medição M-GZ (plano em `specs/patrol-inf/DESIGN.md`, seção 3) sem pedido explícito do Roberto.
- Papel de cada máquina: `docs/contexto/maquinas.md`.

## 4. Limite de memória

O limite abaixo vale **só para o notebook do Roberto** (7,4 GiB de RAM e GPU Intel integrada), que só roda o L0 (Python puro, sem ROS). Ele já travou durante um `docker build` sem limite. O PC do laboratório simula e tem outros recursos.

- No notebook, nunca rode `docker build` nem processos pesados sem limite de memória.
- Use `docker run --memory=X --memory-swap=X`. Para instalar pacotes, use `docker commit` em vez de `docker build`.
- Acompanhe a RAM livre e pare o container se ela cair demais.
- Avise antes de abrir janelas gráficas e testes longos.
- Scripts seguros ficam em `infra/docker/`.
- Em outra máquina, confira primeiro quanta RAM há e ajuste o teto. Na dúvida, use o limite acima.

## 5. Como explicar e planejar para o Roberto

Ele é iniciante em robótica. Um plano com termos soltos e sem links já foi criticado. Ele também rejeita analogias e exemplos do dia a dia: não use nenhum.

- Explique a coisa real, tecnicamente: o que é, como funciona por dentro, por que existe e o que acontece de fato (mecanismo, componentes, números, comportamento). Exemplos só do próprio domínio: um comando real, uma saída real, um caso de código ou de robótica.
- Abra com a resposta direta, responda cada dúvida dele em seção própria, na ordem em que perguntou, e termine com o efeito prático.
- Para cada etapa de um plano, diga o que é e por quê, dê o link exato e a ordem de leitura, comandos testados para praticar e o critério de "pronto".
- Diga o que foi e o que não foi verificado em cada fonte.
- Defina todo termo técnico na primeira vez que usar.

## 6. Regras de entrega (desde 2026-11-16)

Pedido do Roberto, que vale para toda tarefa, nesta máquina e no PC do laboratório:

- **Documento por tarefa.** Ao fim de cada tarefa, crie `docs/tarefas/AAAA-MM-DD-<nome>.md` com a data e a explicação detalhada do pipeline: o que foi feito, em qual arquivo, para que serve, como foi verificado e o que não foi. Abra com a resposta direta, e termine com o efeito prático. Sem analogias.
- **Registro.** O `docs/historico/registro-de-mudancas.md` está congelado. O registro agora é uma linha por tarefa (data, tarefa, documento) na tabela de `docs/tarefas/README.md`. O que mudou fica no documento da tarefa; a tabela só aponta.
- **Código comentado na medida certa.** Comente o porquê das escolhas e o que não é óbvio. Não comente o que o código já diz.
- **Documentação oficial.** Siga a documentação oficial (TurtleBot 4, ROS 2, Nav2, Create 3, slam_toolbox) e cite a página no código ou no documento quando um comando vier dela.
- **Caminhos citados.** Todo caminho entre crases em documento vivo precisa existir: `python3 infra/ferramentas/checar_caminhos.py` confere (e roda no CI).

## 7. Onde achar o resto

Comece pelo `README.md`. Caminhos relativos à raiz do repositório.

| O que | Arquivo |
|---|---|
| Como rodar (índice dos guias) | `docs/guias/como-rodar.md` |
| O que está em aberto | `docs/contexto/pendencias.md` |
| Skills do Claude Code (instalar no PC do lab) | `docs/contexto/skills/README.md` |
| Como acessar o robô | `docs/guias/acesso-ao-robo.md` |
| Escopo, briefing e missões | `docs/contexto/projeto.md` |
| Máquinas, rede e papel de cada uma | `docs/contexto/maquinas.md` |
| Stack e fontes | `docs/contexto/stack.md` |
| Decisões (ADRs e antigas) | `docs/decisoes/README.md` |
| O que foi feito, por tarefa | `docs/tarefas/README.md` |
| Histórico congelado | `docs/historico/` |
| Specs | `specs/README.md` |

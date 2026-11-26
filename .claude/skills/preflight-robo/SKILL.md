---
name: preflight-robo
description: Use antes de a patrulha oficial mover o TurtleBot 4, ou quando o usuário pedir para conferir se o robô, a rede e o Nav2 estão prontos ("preflight", "posso rodar a patrulha?", "confere o robô antes de rodar"). Só lê e, com OK, sobe serviços no PC; nunca move o robô. Responde APROVADO ou REPROVADO, item por item.
allowed-tools: ["Read", "Bash", "AskUserQuestion"]
---

# Preflight da patrulha oficial

Confere PC, rede, robô e Nav2 antes de a patrulha de `workspace/patrulha_oficial/` mover o robô.
Fonte das regras: `specs/preflight-robo/SPEC.md`. Todos os comandos partem da raiz do repositório.
Rode na conversa principal: nenhum subagente alcança o robô.

**Qual robô:** pergunte antes de começar e ponha `ROBO=<nome>` (um perfil de `infra/lab/robos/`)
na frente de **todo** `checar.sh`, `lab.sh robo` e `rodar.sh`. Sem ele vale o do último
`lab.sh robo usar` (veja com `lab.sh robo usar`, sem nome), e depois o `robot1`. As
coordenadas do A8 são as mesmas para todos: confirme a posição da doca do robô escolhido.

## Limites

| Classe | Ações |
|---|---|
| Livre | Ler arquivos, o `scripts/checar.sh`, `ping`, `lab.sh robo checar-rede`, `lab.sh robo estado`, leitura de tópicos e logs |
| Com OK, **um comando por vez** | `lab.sh robo compose stop slam`; `lab.sh robo subir localizacao`, `rviz`, `nav2`; recriar o Nav2; `lab.sh robo parar` (avise que derruba todos os serviços) |
| Proibido | Controle manual, sair ou entrar na doca, patrulha da `patrulha_tb4`, voltar à doca, executar o `rodar.sh`, `lab.sh robo llm` ou `falar`, rodar `patrol_loop.py` sem `--verificar-localizacao`, `loop.py`, `patrol_loop2.py`, enviar meta ou publicar em tópico, `lab.sh robo usar <nome>`, entrar no robô, mudar rede ou configuração do robô, `sudo`, reiniciar ou pausar contêiner pelo `docker` |

Se a correção for no robô ou pedir `sudo`, mostre o comando e a página oficial
([Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html),
[Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html),
[Docking](https://iroboteducation.github.io/create3_docs/api/docking/)); quem roda é o operador.

Item reprovado, sem resposta no prazo ou não verificado resulta em **REPROVADO**. Resposta vaga
do operador não conta como OK nem como confirmação.

## Ordem

Use um só relatório do começo ao fim:

```bash
REL=workspace/logs/preflight_$(date +%F_%H-%M-%S).md
```

### Fase A: antes de subir

```bash
.claude/skills/preflight-robo/scripts/checar.sh A "$REL"
```

Mostre ao operador as coordenadas do A8 e pergunte se são as esperadas
(`workspace/mapas/pontos_mapa_lab_novo.md`). Com item reprovado, não suba nada: informe, proponha a
correção e dê o veredito. Se serviços já estiverem no ar e o item que falhou não for deles, diga.

Se faltarem tópicos do robô (A5), o operador pode rodar **no robô** o que está registrado em 23/11:
`ros2 daemon stop; ros2 daemon start; ros2 topic list`.

### Fase B: subir o que faltar, com OK

Veja antes o que já roda (`infra/docker/lab.sh robo estado`). Não recrie serviço sem motivo.

1. Se o `slam` estiver rodando: `infra/docker/lab.sh robo compose stop slam`
2. `MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao`
3. `infra/docker/lab.sh robo subir rviz`
4. **Pare aqui.** O operador faz o 2D Pose Estimate na pose real da doca e confirma que o laser
   coincide com as paredes.
5. Só depois: `MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2`

Para recriar o Nav2 (nunca com `docker`), cada linha com OK:
`infra/docker/lab.sh robo compose rm -sf nav2` e `infra/docker/lab.sh robo subir nav2`.
`lab.sh robo parar <serviço>` derruba **todos** os serviços.

### Fase C: estabilidade, sem movimento

```bash
.claude/skills/preflight-robo/scripts/checar.sh C "$REL"      # leva mais de 1 minuto
```

Depois, peça ao operador um novo 2D Pose Estimate e, assim que ele confirmar:

```bash
.claude/skills/preflight-robo/scripts/checar.sh C4 "$REL"     # exige map→odom com menos de 2 s
```

### Fase D: confirmação do operador

Pergunte, sem presumir:

1. Há uma pessoa ao lado do robô capaz de pará-lo?
2. A área está livre?
3. O TurtleBot ligado é o do perfil escolhido (etiqueta ou número de série)?
4. O trajeto de volta à doca está livre no costmap do RViz?

## Saída

1. Tabela com item, resultado e evidência (curta).
2. Veredito: **APROVADO** só com todos os itens das fases A a D atendidos; senão **REPROVADO**,
   citando os itens.
3. Acrescente a tabela, as respostas da fase D e o veredito ao relatório e informe o caminho.
4. Com APROVADO, mostre para **o operador** rodar: `workspace/patrulha_oficial/rodar.sh 1`,
   lembrando de refazer o 2D Pose Estimate no prompt dele.

O veredito vale para aquele momento e **não autoriza movimento**.

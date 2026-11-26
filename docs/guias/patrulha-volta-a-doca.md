# Patrulha de ida e volta que termina na doca (robô real)

> **Outro robô:** os exemplos usam o `robot1`. Para outro, rode antes `infra/docker/lab.sh robo usar <nome>` e, nos comandos digitados, troque `/robot1` e o IP pelos dele (`docs/guias/acesso-ao-robo.md`, seção "Vários robôs").

Programa: `workspace/patrulha_oficial/patrol_loop2.py`. Rota: pontos **1 → 2 → 3 → 4 → 3 → 2 → 1** e encaixe na doca. Faz uma única passagem e encerra.

Todos os comandos rodam no PC do laboratório, na raiz do projeto. Os blocos estão na ordem de execução.

> **O robô anda sozinho.** Este programa **não pede `SIM`**: o undock acontece logo depois do Enter no passo 5. Antes disso: robô na doca, área livre e uma pessoa ao lado, pronta para pará-lo.

## 1. Preparar

```bash
cd ~/physical_ai                                  # raiz do projeto
infra/docker/lab.sh robo parar                    # derruba sobras de uma sessão anterior
infra/docker/lab.sh robo checar-rede              # só lê; precisa terminar em "REDE OK"
```

## 2. Subir a localização

```bash
# AMCL + servidor do mapa mapa_lab_novo (não move o robô)
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir localizacao
```

## 3. Subir o Nav2 e o RViz

```bash
# Nav2 (planejamento e controle) + janela do RViz; rodar num terminal da área de trabalho
MAPA=/mapas/mapa_lab_novo.yaml infra/docker/lab.sh robo subir nav2 rviz
infra/docker/lab.sh robo estado                   # localizacao, nav2 e rviz devem aparecer "Up"
```

## 4. Marcar a pose e conferir o Nav2

No RViz, com o robô na doca: **2D Pose Estimate** na posição e direção reais. Os pontos do laser devem cair sobre as paredes do mapa.

```bash
# Mostra se o Nav2 ativou, abortou ou perdeu algum nó
docker logs tb4-robo-nav2-1 2>&1 | grep -E "Managed nodes are active|Aborting bringup|CRITICAL"
```

- Esperado: `Managed nodes are active`, **sem** `CRITICAL` nem `Aborting` depois dele. Espere cerca de 1 minuto e rode de novo, porque os nós já caíram logo após ativar (23/11).
- Se apareceu `Aborting bringup` ou `CRITICAL`, recrie só o Nav2, com a pose já marcada:

```bash
infra/docker/lab.sh robo compose rm -sf nav2      # remove só o contêiner do Nav2
infra/docker/lab.sh robo subir nav2               # cria de novo (não usar "docker restart")
```

## 5. Rodar o programa

Marque o **2D Pose Estimate** de novo imediatamente antes (ou em até 30 s depois do Enter). O programa só anda se a transformação `map→odom` for recente.

```bash
# MOVE O ROBÔ: undock, 1-2-3-4-3-2-1 e dock
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop2.py --ros-args -r __ns:=/robot1
```

Teste opcional antes, **sem movimento** (robô na doca; confere localização e ações do Nav2):

```bash
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop2.py --verificar-localizacao --ros-args -r __ns:=/robot1
```

## 6. Se parou no meio: voltar à doca

Use depois de um `Ctrl+C` ou de uma falha, **somente com o programa anterior já encerrado**. Exige localização e Nav2 ativos e pose recente.

```bash
docker ps                                         # não pode haver outro contêiner "...-ferramentas-run-..." andando o robô
# MOVE O ROBÔ: vai ao ponto 1 e encaixa
infra/docker/lab.sh robo compose run --rm -T ferramentas \
    python3 /workspace/patrulha_oficial/patrol_loop2.py --voltar-doca --ros-args -r __ns:=/robot1
```

## 7. Encerrar (sempre)

```bash
infra/docker/lab.sh robo parar                    # derruba TODOS os serviços do modo robo
docker ps                                         # a lista não deve ter nada "tb4-robo-..."
```

`parar` não é parada de emergência. Para interromper o movimento, use `Ctrl+C` no terminal do programa e confira o robô fisicamente.

## Variante: os quatro pontos em sequência

`workspace/patrulha_oficial/rodar.sh` roda `patrol_loop.py` (1 → 2 → 3 → 4 → doca). Ele confere mapa, rede e contêineres e **pede `SIM`**. Substitui o passo 5; os demais passos são iguais.

```bash
workspace/patrulha_oficial/rodar.sh 1             # MOVE O ROBÔ: 1 volta e dock
```

## Mensagens e códigos de saída

| Código | Significado |
|---|---|
| 0 | Rota concluída e dock confirmado |
| 2 | Robô não confirmado na doca |
| 3 | Bateria ausente ou abaixo de 20% |
| 4 | Undock não confirmado |
| 5 | Falha na volta à doca |
| 6 | Um destino falhou, foi recusado ou passou de 120 s; o programa para onde está |
| 7 | Sem `map→odom` recente (refazer o 2D Pose Estimate) |
| 8 | Ações do Nav2, dock ou undock indisponíveis |
| 130 | Interrompido com `Ctrl+C` |

## Limitações conhecidas

- As falhas de 23/11 no ponto 1 não têm causa determinada. Detalhes em `docs/tarefas/2026-11-23-patrulha-oficial-mapa-lab-novo.md`.
- As coordenadas ficam só em `workspace/patrulha_oficial/patrol_loop.py` (`PONTOS`).

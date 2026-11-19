# Tarefa: spec da migração para Humble, ADRs e prévia do enxugamento

*Nota (2026-11-19): os caminhos deste documento são da época. Depois do enxugamento (`specs/enxugamento/SPEC.md`), o mapa das pastas está no `README.md` da raiz.*

**Data:** 2026-11-18
**Pedido:** analisar as duas frentes (enxugamento e migração Jazzy → Humble), escolher qual especificar primeiro, registrar os pontos do enxugamento numa prévia, abrir a spec da migração pela skill `/sdd`, registrar a decisão em ADR e as mudanças num documento. Cenário novo: o PC do laboratório simula e o robô físico testa. Preferência por `launch.py` em vez de scripts, quando não piorar nada.
**Situação:** só documentos. **Nenhum código, imagem, compose ou script mudou.** A spec e os ADRs foram **aprovados pelo Roberto no portão** em 2026-11-18. A implementação é outra tarefa, a começar pela F0.

## 1. Resposta direta

A migração para Humble foi especificada primeiro. Ela destrava o robô real, parado desde 16/11 porque os nós Jazzy do PC derrubam o robô Humble. Fazer o enxugamento antes significaria organizar textos que a migração reescreve. Os pontos do enxugamento ficaram anotados numa prévia, para virar spec depois.

Decisões do Roberto nesta tarefa:

| Pergunta | Resposta |
|---|---|
| Escopo | Todas as imagens em Humble |
| Como guardar o Jazzy | Tag git `jazzy-final` + imagens `physical-ai:jazzy-<alvo>` no PC |
| Rigor da spec | ADR + DEFINE + DESIGN (padrão da `specs/patrol-inf/`) |
| Simulador principal | Gazebo (Ignition Fortress) no PC do lab, **e** o `nav2_loopback_sim` vendorizado para o L1 |
| Onde ficam os launches | Pacote novo de bringup, `lab_tb4` |

## 2. Arquivos

| Arquivo | O que é | Para quê |
|---|---|---|
| `docs/decisoes/ADR-001-ros2-humble.md` | Decisão: todas as imagens em Humble, Jazzy preservado | Registrar por que e como voltar (até 200 palavras) |
| `docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md` | Decisão: Gazebo no PC é o principal, o leve vendorizado fica como L1 | Revê a decisão de 2026-11-09. É um ADR separado porque é outra decisão |
| `contexto/projeto/decisoes.md` | Duas linhas novas apontando para os ADRs. As linhas antigas de Jazzy e do leve marcam "será substituída" | Manter o índice coerente |
| `specs/migracao-humble/DEFINE.md` | 43 requisitos EARS (IMG, PRE, SEG, LCH, SIM, CFG, CI, DOC) | O **o quê**, testável |
| `specs/migracao-humble/DESIGN.md` | Três camadas, imagens, `lab_tb4`, compose, scripts, `pkg://`, inventário, fases F0 a F4, verificações V1 a V5, rastreio, riscos | O **como** |
| `specs/enxugamento/PREVIA.md` | Pontos anotados para a próxima spec | Não perder o que apareceu na análise |
| `docs/registro-de-mudancas.md` | Entrada do dia | Regra de entrega |

## 3. O pipeline da spec, peça por peça

### 3.1 Por que três camadas (host, containers, ROS)

Um `launch.py` roda dentro do container. Ele não enxerga o Docker, as rotas do PC nem o terminal do usuário. Por isso a preferência por launches tem um limite claro:

- **Shell no host:** subir e derrubar containers, conferir rotas, xhost, pedir `SIM`, guardar evidências.
- **Compose:** um serviço por processo pesado, porque o teto de memória (`mem_limit`) só existe por container.
- **`launch.py`:** compor nós ROS. Hoje há dois lugares onde shell faz esse papel: o `l1_dentro.sh`, que sobe Nav2, base falsa e patrulha em segundo plano com `&`, e o bind-mount do `sim_headless.launch.py` por cima de um arquivo de `/opt/ros/jazzy/share/`. Os dois viram launches do `lab_tb4`.

A única orquestração que fica fora do launch é a retentativa do Nav2 leve ("Aborting bringup"). O launch do ROS 2 não tem um jeito de reiniciar um include inteiro. Por isso o `vigia_l1` sai com o código 10 e o `teste_l1.sh` roda o container de novo. O motivo está no DESIGN, seção 5.

### 3.2 Por que o entrypoint

Hoje cada serviço do compose começa com `bash -c "source /opt/ros/jazzy/setup.bash && ..."`. São 14 ocorrências no `robo.yaml` e 10 no `sim.yaml`. As imagens oficiais `ros:*` já gravam a variável `ROS_DISTRO`, e o entrypoint novo carrega `/opt/ros/$ROS_DISTRO/setup.bash`. Com isso, a próxima troca de distro mexe só no Dockerfile (IMG-03, IMG-04).

### 3.3 Por que a guarda SEG-01

O incidente de 16/11 foi evitado depois só por avisos em texto ("não use o `lab.sh robo`"). A SEG-01 transforma isso em checagem. Antes de qualquer ação do modo `robo`, o `lab.sh` lê o `ROS_DISTRO` de cada imagem do `robo.yaml` (`docker image inspect`) e recusa se não for `humble`. Isso ataca a classe do problema ("distro diferente na rede do robô"), e não só o caso de 16/11.

### 3.4 Por que o `pkg://` nas configurações

Quatro configs têm `/opt/ros/jazzy/share/turtlebot4_navigation/maps/...` escrito direto. Com `pkg://turtlebot4_navigation/maps/maze.yaml`, o `config.py` resolve o caminho pelo ament_index, que acha o pacote na distro instalada (CFG-01). O `import` fica dentro da função para os testes L0 continuarem rodando no notebook sem ROS.

### 3.5 O que foi conferido na documentação oficial (GitHub, ramos `humble`)

- `turtlebot4_ignition.launch.py` aceita `namespace`, `rviz`, `world`, `model` e a pose, mas **não** aceita `slam`, `localization` nem `nav2`, e não tem modo servidor. Por isso existe o `gazebo.launch.py` nosso.
- O `turtlebot4_viz` do Humble não tem `view_navigation.launch.py`, só `view_robot.launch.py`.
- O `nav2_loopback_sim` (jazzy) é Python puro e depende de `tf_transformations`, `transforms3d` e `nav2_simple_commander.line_iterator`. O vendor é viável. A V3 confirma.

### 3.6 Ordem de implementação

F0 (preparo e tag) → **F1 (robô: `base`/`robo` Humble, SEG-01, perfil Nav2)** → F2 (Gazebo) → F3 (L1 vendorizado) → F4 (limpeza, CI, docs). A F1 vem primeiro porque sozinha já destrava o robô, e o prazo é por volta de 20/dez.

## 4. Verificado e não verificado

| Item | Situação |
|---|---|
| Args do `turtlebot4_ignition.launch.py`, launches do `turtlebot4_viz` e do `turtlebot4_navigation`, pacotes do `turtlebot4_tutorials` (Humble) | **Lido** no GitHub, ramos `humble` |
| Dependências e imports do `nav2_loopback_sim` (jazzy) | **Lido** no GitHub |
| Uso do `TurtleBot4Navigator` pelo `no_patrulha.py` | **Lido** no código local (linhas 166 a 321) |
| ADRs com até 200 palavras | **Medido** com `wc -w`: 180 e 174, antes da linha de retorno do ADR-001 |
| Crítica EARS do DEFINE | **Feita** pelo subagente `sdd-ears-critico` (1 rodada): 23 dos 32 critérios tinham problema (composto, gatilho vago, linha de base "de hoje" sem commit). Todos foram reescritos ou divididos, e o DEFINE passou a 43 IDs. A base de comparação agora é a tag `jazzy-final` |
| Nomes internos do `TurtleBot4Navigator` Humble (`dock_action_client` etc.) | **Não verificado** (V2) |
| Loopback vendorizado roda no Humble | **Não verificado** (V3) |
| `--headless-rendering` no Fortress, `stamped` no teleop Humble, `maps/` no `turtlebot4_navigation` Humble | **Não verificado** (DESIGN, seção 2, "a conferir") |

## 5. Efeito prático

- O próximo passo é a F0: escolher o texto que fica nas marcas de conflito do `registro-de-mudancas.md` e do `kit-de-campo.md`, commitar o que está pendente e criar a tag `jazzy-final`.
- Com a F1 pronta, o robô volta a ser testável. A SEG-01 impede que o incidente de 16/11 se repita por engano.
- Para a banca: a troca de distro tem motivo medido (16/11), decisão registrada (ADR-001), requisitos testáveis e caminho de volta (`jazzy-final`).

# DESIGN: migração das imagens e da infra para ROS 2 Humble

**Status:** Aprovado em 2026-11-18 (portão da skill `/sdd`)
**Data:** 2026-11-18
**Base:** `DEFINE.md` desta pasta, ADR-001 e ADR-002 (`docs/decisoes/`)

## 1. Resposta direta

A migração tem três peças:

1. **Imagens Humble.** O Dockerfile troca a base para `ros:humble-ros-base`, fica com 4 alvos e ganha um entrypoint que carrega o ROS pela variável `ROS_DISTRO`. Os compose deixam de escrever `source /opt/ros/jazzy/setup.bash`, e a próxima troca de distro mexe só no Dockerfile.
2. **Um pacote de bringup, o `lab_tb4`.** Os nós que hoje são compostos por shell (`l1_dentro.sh`, o bind-mount do `sim_headless.launch.py`) passam para `launch.py`. O shell fica só com o que é do host: Docker, rede, rotas, xhost, a confirmação `SIM` e as evidências.
3. **Simuladores.** O Ignition Fortress sem janela no PC do lab é o principal (ADR-002). O `nav2_loopback_sim` é vendorizado para manter os 11 cenários L1.

A ordem de implementação põe o robô primeiro (F1), porque ele é o que está parado e o prazo está perto.

## 2. Fatos verificados (2026-11-18)

| Fato | Fonte | Impacto |
|---|---|---|
| O simulador do TB4 no Humble é o `turtlebot4_ignition_bringup`. O `turtlebot4_ignition.launch.py` aceita `namespace`, `rviz`, `world`, `model`, `x`, `y`, `z` e `yaw`. Não aceita `slam`, `localization` nem `nav2`, e não tem modo servidor | github.com/turtlebot/turtlebot4_simulator, ramo `humble` | O `gazebo.launch.py` nosso inclui o `ignition.launch.py` com `-s` e o `turtlebot4_spawn.launch.py`. SLAM e Nav2 continuam como serviços separados |
| O `ignition.launch.py` (Humble) chama o `ign_gazebo.launch.py` com `-r -v 4` e um `gui.config` | idem | Precisamos do nosso launch para passar `-s` (só servidor) |
| O `turtlebot4_viz` do Humble só tem `view_robot`, `view_model` e `view_diagnostics` | turtlebot4_desktop, ramo `humble` | O serviço `rviz` usa o `view_robot.launch.py` |
| O `turtlebot4_navigation` do Humble tem `slam`, `localization` e `nav2.launch.py`, e o `TurtleBot4Navigator` com `dock`, `undock`, `getDockedStatus` e `startToPose` | turtlebot4, ramo `humble` | Os serviços `slam`, `localizacao` e `nav2` só trocam de distro. Os atributos internos que o nosso nó usa são conferidos na V2 |
| O `turtlebot4_tutorials` (Humble) tem `python_tutorials` e `openai_tutorials` | turtlebot4_tutorials, ramo `humble` | O alvo `llm` continua compilando do GitHub, agora com `-b humble` |
| O `nav2_loopback_sim` (jazzy) é ament_python. Depende de `tf_transformations`, `python3-transforms3d` e `nav2_simple_commander.line_iterator`, e publica um `LaserScan` tirado do mapa | navigation2, ramo `jazzy` | O vendor é viável. Falta conferir se o `line_iterator` existe no Humble (V3); se não existir, ele também é vendorizado |
| O `nav2_inf_devagar.yaml` é cópia do nav2.yaml do Jazzy: tem `enable_stamped_cmd_vel` em 10 servidores e um `docking_server` | `config/nav2_inf_devagar.yaml` | É regenerado do Humble (CFG-04), e o `sed` do STAMPED sai |
| O `config.py` já aplica `expandvars` e `expanduser` no `mapa` (linha 140) | `patrulha_tb4/config.py` | O `pkg://` (CFG-01) entra antes dessa linha |
| O `no_patrulha.py` usa `nav_to_pose_client`, `dock_action_client`, `undock_action_client`, `goal_handle`, `result_future`, `status`, `setInitialPose`, `waitUntilNav2Active` e `goToPose` | `no_patrulha.py:166-321` | A V2 confere cada um no código Humble |

**A conferir na implementação:**

- O Fortress aceita `--headless-rendering`? Se não aceitar, o lidar renderiza no Xvfb, como hoje.
- O `teleop_twist_keyboard` do Humble tem o parâmetro `stamped`? Se não tiver, o parâmetro sai do compose.
- O `turtlebot4_navigation` do Humble traz `maps/maze.yaml` e `maps/warehouse.yaml`?
- O nome do mundo `maze` existe no `turtlebot4_ignition_bringup`?

## 3. Três camadas

| Camada | Arquivos | Responsabilidade | Por que nesta camada |
|---|---|---|---|
| Host | `lab.sh`, `construir_imagem.sh`, `teste_l1.sh` | Docker, rede e rotas, xhost, `SIM`, guarda de distro, pasta de evidências, veredito | Um `launch.py` roda dentro do container e não enxerga o Docker, as rotas do PC nem o terminal do usuário |
| Containers | `compose/sim.yaml`, `compose/robo.yaml` | Um serviço por processo pesado, com o próprio teto de memória e o próprio `profile` | O teto por processo (`mem_limit`) só existe no nível do container. Juntar o Gazebo e o Nav2 num launch só perde esse teto |
| ROS | `lab_tb4/launch/*.launch.py` | Compõe nós, argumentos, condições e o `OnProcessExit` | É a ferramenta do ROS para isso: argumentos tipados (`--show-args`), `IncludeLaunchDescription` dos launches oficiais e encerramento coordenado |

Regra prática (LCH-02): se a tarefa é "subir N nós ROS juntos", vai para um `launch.py`. Se é "falar com o Docker ou com o usuário", vai para o shell.

## 4. Imagens

```dockerfile
# base: Nav2, SLAM, teleop, o que o patrulha_tb4 e o lab_tb4 precisam. Sem janela.
FROM ros:humble-ros-base AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-humble-turtlebot4-navigation ros-humble-nav2-bringup \
      ros-humble-nav2-simple-commander ros-humble-slam-toolbox \
      ros-humble-irobot-create-msgs ros-humble-teleop-twist-keyboard \
      ros-dev-tools python3-yaml python3-pytest \
    && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

# robo: base + RViz (turtlebot4_desktop)
FROM base AS robo
RUN apt-get update && apt-get install -y --no-install-recommends ros-humble-turtlebot4-desktop \
    && rm -rf /var/lib/apt/lists/*

# sim: robo + Ignition Fortress com o TB4 + o que o loopback vendorizado precisa
FROM robo AS sim
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-humble-turtlebot4-simulator ros-humble-tf-transformations python3-transforms3d xvfb \
    && rm -rf /var/lib/apt/lists/*

# llm: base + tutoriais (ramo humble), como hoje
FROM base AS llm
# git clone -b humble turtlebot4_tutorials + colcon build (python_tutorials, openai_tutorials)
```

O `entrypoint.sh` (novo, em `infra/docker/`):

```bash
#!/usr/bin/env bash
# Carrega o ROS da distro da imagem (ROS_DISTRO vem da imagem oficial) e o overlay, se houver.
source "/opt/ros/${ROS_DISTRO}/setup.bash"
[ -f /opt/tb4_ws/install/setup.bash ] && source /opt/tb4_ws/install/setup.bash
exec "$@"
```

O que sai da imagem: o alvo `completa`, `turtlesim`, `demo_nodes_py`, `x11-apps` e o `mesa-utils`. Estes eram de estudo ou de diagnóstico no notebook. O `mesa-utils` volta se o RViz no PC precisar de `glxinfo` para diagnóstico.

O `construir_imagem.sh` perde o `apelidos` (só existia para o `docker commit` do notebook) e ganha o PRE-02:

```bash
DISTRO_ANTIGA=jazzy   # a distro que o PRE-02 guarda (exceção do IMG-04)
# PRE-02: antes do build de cada alvo, guarda a imagem antiga que tem o mesmo nome.
# Roda DEPOIS da conferência de RAM (IMG-06): numa máquina recusada, nem a tag é criada.
distro_de() { docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" 2>/dev/null \
              | sed -n 's/^ROS_DISTRO=//p'; }
if [ "$(distro_de "${NOME[$alvo]}")" = "$DISTRO_ANTIGA" ]; then
  docker tag "${NOME[$alvo]}" "physical-ai:$DISTRO_ANTIGA-$alvo"
fi
```

## 5. Pacote `lab_tb4`

```text
workspace/meu_ws/src/lab_tb4/
├── package.xml, setup.py, setup.cfg, resource/lab_tb4
├── lab_tb4/
│   ├── base_falsa.py       # = infra/tools/fake_tb4_base.py (LCH-03), entry point base_falsa
│   ├── conferir_l1.py      # = infra/tools/conferir_l1.py; roda sem ROS (o host chama com python3)
│   └── vigia_l1.py         # o laço do l1_dentro.sh: ponto pronto, tempo-limite, SIGINT, retentativa
├── launch/
│   ├── gazebo.launch.py    # Fortress -s + spawn do TB4 (SIM-01)
│   ├── sim_leve.launch.py  # loopback + map_server + navigation do Nav2 + base falsa (SIM-03)
│   └── l1.launch.py        # cenario:=X -> sim_leve + patrulha.launch.py + vigia_l1 (SIM-04 a 06)
├── config/
│   └── cenarios_l1.yaml    # os 11 cenários: parâmetros da base, config, limite, extras (SIM-04)
└── test/                   # L0 do conferir_l1 e do leitor de cenarios_l1.yaml
```

### `gazebo.launch.py`

- Argumentos: `world` (padrão `maze`), `model` (padrão `standard`), `namespace` (padrão vazio).
- Inclui o `ros_ign_gazebo/launch/ign_gazebo.launch.py` com `ign_args: <world>.sdf -s -r -v 2` (servidor sem GUI) e o `turtlebot4_ignition_bringup/launch/turtlebot4_spawn.launch.py`. Ele copia do `ignition.launch.py` oficial o resto do que é preciso: a ponte do `/clock` e as variáveis de recurso.
- Substitui o bind-mount atual por cima de `/opt/ros/jazzy/share/...`. Esse bind-mount quebra sem aviso se o arquivo oficial mudar.
- O Xvfb continua no `command` do serviço se o `--headless-rendering` não existir no Fortress (seção 2).

### `sim_leve.launch.py`

- Argumentos: `map`, `params_file` (padrão: o `nav2.yaml` do `turtlebot4_navigation`), `rviz` (padrão `false`) e os parâmetros da base falsa.
- Nós: `robot_state_publisher` com o URDF do `turtlebot4_description`, `map_server` + `lifecycle_manager`, `nav2_bringup/launch/navigation_launch.py` (Humble), o `loopback_simulator` vendorizado e `lab_tb4 base_falsa`.
- É o equivalente Humble do `tb4_loopback_simulation.launch.py` do Jazzy, que não existe no Humble.

### `l1.launch.py` e `vigia_l1`

- **Desvio no `l1b` (F3):** o `nav2_extra: params_file:=/tmp/nav2_l1b.yaml` do Jazzy vira `nav2_perfil:=turtlebot4`. O perfil em `/tmp` só existia para ligar o `enable_stamped_cmd_vel` do loopback contra o `TwistStamped` do Nav2 Jazzy. No Humble tudo é `Twist`, e basta trocar o perfil.
- `cenario:=<nome>` lê o `cenarios_l1.yaml` e monta os parâmetros da base, a configuração da patrulha e o limite de tempo, o que hoje o `case` do `teste_l1.sh` faz.
- O `vigia_l1` é um nó Python que faz o laço do `l1_dentro.sh`. Ele confere o JSONL com `conferir_l1 --pronto`, aplica o tempo-limite e manda o SIGINT para a patrulha (PAT-15). Também procura `Aborting bringup` no log do Nav2 e pede a retentativa (SIM-06).
- **Ponto de atenção:** a retentativa exige derrubar e subir de novo um include inteiro. O launch do ROS 2 não tem "reiniciar include". Proposta: se o `vigia_l1` achar `Aborting bringup` no `/rosout` nos primeiros `[15 s]`, ele grava o marcador `nav2_abortou` na pasta de evidências e encerra o launch. **Ajuste da implementação (F3, 2026-11-18):** a proposta original era o código de saída `10`, mas o código de saída do `ros2 launch` não reflete o de um nó, então o sinal passou a ser o arquivo marcador. Pelo mesmo motivo, o vigia sobe junto com o Nav2 (aos 0 s), e não com a patrulha (aos 18 s): senão perderia o log. O `teste_l1.sh` (host) então roda o cenário de novo num container novo, até `[3]` tentativas, e anota cada uma no `nav2_tentativas.txt` (SIM-06). Esgotadas as tentativas, o veredito é `REPROVADO`, com o motivo `nav2_nao_subiu` (SIM-06b). Assim a retentativa fica no host, que já é dono do ciclo de vida do container. Isso muda o comportamento de hoje: o `l1_dentro.sh` reinicia só os processos do Nav2, e não o container inteiro. É a única lógica de orquestração que fica fora do launch, e o motivo está aqui.

### Loopback vendorizado

- Fica em `workspace/meu_ws/src/terceiros/nav2_loopback_sim/`, copiado de `ros-navigation/navigation2`, ramo `jazzy`, com o SHA no `ORIGEM.md`.
- Patches esperados (a confirmar na V3): `line_iterator` copiado junto, se o `nav2_simple_commander` do Humble não tiver esse módulo; e `enable_stamped_cmd_vel` com padrão `false`, porque o Nav2 Humble publica `Twist`.
- O `checar_rastreio` e o ruff não leem a pasta `terceiros/`. Ela entra no `exclude` do `ruff.toml`, para não reescrevermos código de terceiros.

## 6. Compose

Padrão para todo serviço: `command: ros2 launch <pacote> <launch> <args>`, sem `bash -c "source ..."`. O entrypoint carrega o ROS.

| Serviço | `robo.yaml` | `sim.yaml` |
|---|---|---|
| `gazebo` | não existe | `ros2 launch lab_tb4 gazebo.launch.py world:=${MUNDO:-maze}`; o pacote é compilado no início, como a `patrulha` faz hoje |
| `leve` | não existe | `ros2 launch lab_tb4 sim_leve.launch.py map:=...` (novo: o L1 interativo no PC) |
| `slam`, `localizacao` | só troca de distro | idem, com `use_sim_time:=true` |
| `nav2` | `params_file:=/workspace/.../nav2_inf_devagar.yaml` direto, **sem a cópia com `sed`** | o `nav2.yaml` oficial |
| `rviz` | `turtlebot4_viz view_robot.launch.py` | idem |
| `teleop` | `stamped` sai ou fica `false`, a conferir (seção 2) | idem |
| `patrulha` | igual, com o `SIM` | igual |

A compilação do workspace dentro do container (`colcon build ... --build-base /tmp/build`) se repete na `patrulha`, no `gazebo` e no `leve`. Ela vai para uma função do `entrypoint.sh`, ligada pela variável `COMPILAR_WS=patrulha_tb4,lab_tb4`. Assim fica uma linha por serviço, e não um bloco copiado três vezes.

## 7. Scripts de host

### `lab.sh`: guarda de distro (SEG-01)

```bash
DISTRO_ESPERADA=humble   # a única distro escrita num script de host (IMG-04)
exigir_distro() {
  local img distro
  for img in $(docker compose -f infra/compose/robo.yaml --profile '*' config --images | sort -u); do
    distro=$(distro_de "$img")
    if [ "$distro" != "$DISTRO_ESPERADA" ]; then
      echo "RECUSADO (SEG-01): a imagem $img tem ROS_DISTRO='${distro:-sem variável}'."
      echo "O robô é $DISTRO_ESPERADA. Outra distro na rede dele pode derrubá-lo (2026-11-16)."
      exit 1
    fi
  done
}
```

Ela é chamada no começo de toda ação do modo `robo`, antes do `exigir_sozinho`. O `ferramenta()` perde o `source /opt/ros/jazzy`. O `salvar` também.

### `teste_l1.sh`

Fica no host e faz menos coisa. O `case` dos cenários sai (vai para o `cenarios_l1.yaml`). A imagem passa a ser `physical-ai:sim`. O comando do container vira `ros2 launch lab_tb4 l1.launch.py cenario:=$CENARIO pasta:=/evidencias`. Continuam no host: a pasta de evidências, a amostra de RAM, o `OOMKilled`, a retentativa pelo marcador `nav2_abortou` e o veredito com o `conferir_l1.py`. O TST-06 (guarda de memória) continua: no PC do lab ele não atrapalha, e a revisão dele é da spec de enxugamento.

## 8. Configurações (CFG-01 a CFG-04)

No `config.py`, antes do `expandvars` da linha 140:

```python
def resolver_pkg(mapa, share=None):
    """pkg://<pacote>/<caminho> -> <share do pacote>/<caminho>. Sem ROS, aceita outro resolvedor (testes)."""
    if not mapa.startswith('pkg://'):
        return mapa
    pacote, _, resto = mapa[len('pkg://'):].partition('/')
    if share is None:
        from ament_index_python.packages import get_package_share_directory as share
    try:
        return os.path.join(share(pacote), resto)
    except Exception:  # PackageNotFoundError, ou ament_index ausente
        raise ConfigInvalida('mapa_pacote_inexistente', pacote)
```

O `import` fica dentro da função para os testes L0 continuarem rodando no notebook sem ROS. As configs passam a usar, por exemplo, `mapa: pkg://turtlebot4_navigation/maps/maze.yaml`.

O `nav2_inf_devagar.yaml` é copiado de `/opt/ros/humble/share/turtlebot4_navigation/config/nav2.yaml` na imagem `base` nova, mudando só o `velocity_smoother` (0,26 para 0,15 m/s em x). O cabeçalho registra a versão do pacote (`dpkg -s ros-humble-turtlebot4-navigation`). A versão Jazzy fica na tag `jazzy-final`.

## 9. Inventário

| Item | Destino | Fase |
|---|---|---|
| `infra/docker/Dockerfile` | Refatora (seção 4) | F1 (`base`, `robo`), F2 (`sim`), F4 (`llm`) |
| `infra/docker/entrypoint.sh` | Novo | F1 |
| `infra/docker/construir_imagem.sh` | Refatora: sem `apelidos` e sem `completa`, com o PRE-02 | F1 |
| `infra/docker/lab.sh` | Refatora: SEG-01, sem distro escrita | F1 |
| `infra/compose/robo.yaml` | Refatora (seção 6) | F1 |
| `patrulha_tb4/config/nav2_inf_devagar.yaml` | Regenerado do Humble | F1 |
| `patrulha_tb4/config.py` + configs | `pkg://` (CFG-01 a CFG-03) | F1 |
| `infra/compose/sim.yaml` | Refatora: `gazebo` via launch, serviço `leve` novo | F2 |
| `infra/docker/sim_headless.launch.py` | Vira `lab_tb4/launch/gazebo.launch.py` | F2 |
| `infra/tools/fake_tb4_base.py` | Vira `lab_tb4/base_falsa.py` | F2 |
| `workspace/meu_ws/src/terceiros/nav2_loopback_sim/` | Novo (vendor) | F3 |
| `infra/docker/l1_dentro.sh` | Vira `l1.launch.py` + `vigia_l1.py`; o arquivo sai | F3 |
| `infra/tools/conferir_l1.py` | Vai para `lab_tb4/conferir_l1.py` | F3 |
| `infra/docker/teste_l1.sh` | Refatora (seção 7) | F3 |
| `infra/docker/run_sim_headless.sh` | Sai: o `lab.sh sim subir gazebo` cobre | F4 |
| `infra/docker/ros.sh` | Sai: terminal de estudo do notebook | F4 |
| `infra/docker/treino_leve.sh` | Sai: rodava o `patrol_loop` oficial no leve; o L1 nosso cobre | F4 |
| `.github/workflows/ci.yml` | Matriz só `humble` (CI-01) | F4 |
| `infra/lab/rede_lab.env` | Mantém: confere o RMW e o Discovery no Humble | F1 (V5) |
| `docs/guias/como-rodar.md`, `kit-de-campo.md`, `pendencias.md`, adendo da `patrol-inf` | DOC-01 a DOC-03 | F4 |

## 10. Fases

| Fase | Entrega | Pronto quando |
|---|---|---|
| F0 | Conflitos de merge resolvidos (escolha do Roberto), pendências commitadas, tag `jazzy-final`, imagens Jazzy com tag `jazzy-<alvo>` no PC | `git tag -n jazzy-final` e `docker images 'physical-ai'` mostram as duas coisas |
| F1 | Imagens `base` e `robo` Humble, `robo.yaml`, SEG-01, perfil Nav2 Humble, `pkg://` | V1, V2 e V5 aprovadas. **Isto destrava o robô** |
| F2 | `lab_tb4` com `gazebo.launch.py` e `base_falsa`, imagem `sim`, `sim.yaml` | Gazebo sobe sem janela e o SLAM gera o mapa `maze` (repete o teste de 16/11) |
| F3 | Loopback vendorizado, `sim_leve` e `l1.launch.py`, `teste_l1.sh` enxuto | V3 aprovada e os 11 cenários com veredito APROVADO |
| F4 | Scripts obsoletos removidos, CI só Humble, documentação | DOC-01 a DOC-03 cumpridos, CI verde |

## 11. Verificações

| ID | O quê | Onde | Critério |
|---|---|---|---|
| V1 | Build das imagens Humble | PC do lab | O build termina. Tamanho e tempo anotados (`docker images`). `docker run --rm physical-ai:base printenv ROS_DISTRO` responde `humble` |
| V2 | API do `TurtleBot4Navigator` e do `BasicNavigator` Humble | Imagem `base` (leitura do código) | Os 9 atributos/métodos da seção 2 existem com o mesmo nome e o mesmo papel. O que diferir vira patch no `no_patrulha.py`, com teste |
| V3 | Loopback vendorizado | PC do lab, imagem `sim` | O Nav2 fica ativo e o robô simulado chega a 1 destino de 2 m no `maze` |
| V4 | M-GZH: Fortress sem janela | PC do lab | Fator de tempo real, pico de RAM, `/battery_state`, doca, lidar com obstáculo e 1 destino de 2 m. **Só com pedido explícito do Roberto** |
| V5 | Robô real com a imagem Humble | PC do lab + TurtleBot 4 | 1) `checar-rede` com `REDE OK`; 2) `subir slam rviz` sem erro no `journalctl` do serviço `turtlebot4` do robô durante 5 min. **Ação crítica: antes, permissão do Roberto e a página da documentação oficial citada (setup/discovery_server.html e tutorials/generate_map.html, aba Humble)** |
| L0 | pytest do `patrulha_tb4` e do `lab_tb4` | Notebook e CI | Tudo passa. Os testes do `pkg://` usam um resolvedor falso |
| G1 | `git grep -nE 'jazzy\|humble' -- infra/compose infra/docker/*.sh \| grep -vE '^[^:]+:[0-9]+:\s*#'` | Notebook | Só as linhas `DISTRO_ESPERADA=` (`lab.sh`) e `DISTRO_ANTIGA=` (`construir_imagem.sh`) |
| G2 | `git grep -n '/opt/ros/' -- workspace/meu_ws/src/patrulha_tb4/config \| grep -vE '^[^:]+:[0-9]+:\s*#'` | Notebook | Nenhuma linha |
| G3 | `grep -nE '(ros2 (launch\|run)).*(&\s*$\|nohup\|setsid)\|(nohup\|setsid).*ros2 (launch\|run)' infra/docker/*.sh` | Notebook | Nenhuma linha (LCH-02) |
| G4 | `grep -nE 'stamped:=true\|enable_stamped_cmd_vel: true' infra/compose/robo.yaml workspace/meu_ws/src/patrulha_tb4/config/nav2_inf_devagar.yaml` | Notebook | Nenhuma linha (SEG-02) |
| G5 | Diff dos `declare_parameter` (nome e padrão) do `lab_tb4/base_falsa.py` contra o `git show jazzy-final:Roberto/infra/tools/fake_tb4_base.py` | Notebook | 11 parâmetros iguais (LCH-03) |

## 12. Rastreio requisito → verificação

| Requisito | Verificação |
|---|---|
| IMG-01, IMG-01b | `grep -n '^FROM' Dockerfile` e `grep -oE 'ros-[a-z0-9-]+' Dockerfile` (todo `ros-` é `ros-humble-` ou `ros-dev-tools`) |
| IMG-02 | Leitura do Dockerfile + V1 (`docker images 'physical-ai'`) |
| IMG-03 | V1: `docker run --rm physical-ai:base ros2 pkg list` funciona sem `source` |
| IMG-04 | G1 |
| IMG-05 | V1: `docker run --rm physical-ai:sim dpkg -l ros-humble-turtlesim ros-humble-demo-nodes-py x11-apps` não acha nenhum |
| IMG-06 | `construir_imagem.sh base` no notebook (7,4 GiB) sai com o código 1, e `docker images` não muda |
| PRE-01 | F0: `git cat-file -t jazzy-final` responde `tag`, e `git show jazzy-final:Roberto/infra/docker/Dockerfile \| grep '^FROM'` mostra só `ros:jazzy-ros-base` e estágios internos |
| PRE-02 | F0/F1: depois do primeiro build Humble, `docker images 'physical-ai'` lista `jazzy-base`, `jazzy-robo` e `jazzy-sim` |
| PRE-03 | `grep` dos dois comandos no ADR-001 |
| SEG-01 | `docker tag physical-ai:jazzy-base physical-ai:base`, depois `./lab.sh robo estado`: sai com o código 1 e mostra a distro (sem rede e sem robô). Depois, volta a tag Humble |
| SEG-02 | G4 + `ros2 topic info -v /robot1/cmd_vel` na V5 mostra só `geometry_msgs/msg/Twist` |
| SEG-03 | `docker compose -f infra/compose/robo.yaml config` sem `--profile` lista zero serviços para subir |
| SEG-04 | `./lab.sh robo teleop` com a resposta `nao`: encerra sem nó (container `ferramentas` fora do robô, ou com o robô desligado) |
| SEG-05 | Leitura do `command` + `CONFIG=` com o modelo vazio: `validar_pontos` recusa e a patrulha não sobe (no `sim`) |
| SEG-06 | `grep -nE 'send_goal\|/dock\|/undock' infra/compose/robo.yaml` sem linha de código |
| LCH-01 | `ros2 launch lab_tb4 <arquivo> --show-args` funciona para os três |
| LCH-02 | G3 + leitura dos `docker run`/`exec` |
| LCH-03 | G5 + `ros2 run lab_tb4 base_falsa` publica `/battery_state` |
| LCH-04 | `git diff jazzy-final -- .../launch/patrulha.launch.py` sem mudança nos nós declarados |
| SIM-01, SIM-01b, SIM-01c | F2: `ros2 topic echo --once` de cada tópico dentro de `[90 s]`; `pgrep -af 'ign gazebo'` sem `-g`; `/battery_state` em 60 s simulados. Isto é o teste de fumaça da F2, e não a medição M-GZH |
| SIM-02, SIM-02b | `docker compose config --services` nos dois arquivos + diff dos `command` normalizados |
| SIM-03, SIM-03b | V3: `ros2 lifecycle get` de cada servidor, `ros2 topic echo --once` de `/odom`, `/tf`, `/battery_state`; `pgrep rviz2` com e sem `rviz:=true` |
| SIM-04, SIM-04b | F3: os 11 cenários; `./teste_l1.sh xyz` lista e não cria container; diff dos valores do YAML contra o `case` do `teste_l1.sh` da `jazzy-final` |
| SIM-05 | F3: listar a pasta de um cenário normal e de um cenário com `LIMITE_S` forçado a 10 s |
| SIM-06, SIM-06b | F3: forçar a falha do Nav2 leve (por exemplo, mapa inexistente) e conferir o `nav2_tentativas.txt` e o `REPROVADO nav2_nao_subiu` |
| SIM-07 | Leitura do `ORIGEM.md` + `diff -r` contra o upstream no SHA citado mostra só os patches listados |
| CFG-01, CFG-02, CFG-02b | L0: testes novos em `test_config.py`, com resolvedor falso e com `ament_index` ausente |
| CFG-03 | G2 |
| CFG-04 | Diff sem comentários contra o `nav2.yaml` da imagem `base` mostra só os 2 valores |
| CFG-05 | `git diff jazzy-final --stat` sem `decisao.py` e sem testes além do `test_config.py`; L0 passa |
| CI-01 | Leitura + run verde no GitHub |
| DOC-01 | O `grep` do próprio requisito, depois do registro da V5 |
| DOC-02 | Extração dos comandos dos blocos de código + `--show-args` na imagem `sim` |
| DOC-03, DOC-04 | Leitura na F4 |

## 13. Riscos

| Risco | Efeito | Resposta |
|---|---|---|
| O loopback vendorizado depende de algo do Nav2 Jazzy além do `line_iterator` | A F3 atrasa | Se a V3 reprovar, escrevemos um loopback mínimo nosso (integra o `cmd_vel`, publica `odom`, TF e o `scan` do mapa) |
| O Fortress sem GPU dedicada renderiza o lidar devagar | Gazebo lento como principal | A V4 mede. Se reprovar, o leve volta a ser o principal (o ADR-002 é revisto) |
| Os nomes internos do `TurtleBot4Navigator` mudam no Humble | Patrulha quebra no robô | A V2 pega antes da V5 |
| O Nav2 Humble tem parâmetros diferentes no perfil | O robô anda diferente do esperado | O CFG-04 copia o perfil oficial Humble e muda só a velocidade |
| A F2 a F4 tomam o tempo do robô | Prazo de 20/dez | A F1 vem primeiro e sozinha já destrava o robô |

## 14. Efeito prático

- Depois da F1, o `lab.sh robo` volta a ser usável. A guarda SEG-01 impede que uma imagem de outra distro chegue à rede do robô de novo, sem depender de alguém lembrar do aviso.
- A próxima troca de distro (de volta ao Jazzy, ou para o próximo LTS) muda o `FROM` e os nomes dos pacotes no Dockerfile. Os compose e os scripts não mudam.
- Os ambientes passam a ser `ros2 launch lab_tb4 ...`, com argumentos que o `--show-args` lista. Quem chega na equipe lê os launches, e não precisa seguir `bash -c` dentro de YAML.
- Para a banca, a pergunta "por que Humble?" tem resposta com data e medição: o incidente de 16/11 e o ADR-001.

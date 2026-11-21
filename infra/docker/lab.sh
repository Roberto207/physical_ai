#!/usr/bin/env bash
# Atalho para os serviços do Docker Compose (infra/compose/sim.yaml e robo.yaml). Faz só o que
# o Compose não faz sozinho: conferir a rede, liberar a tela, salvar o mapa com a ficha e
# impedir o sim e o robo de rodarem juntos.
#
#   ./lab.sh <sim|robo> subir <serviço...>   sobe em segundo plano (ex.: subir gazebo slam rviz)
#   ./lab.sh robo checar-rede                só lê: rotas, e /scan, /tf e /odom do robô chegam ao PC?
#   ./lab.sh sim undock                      tira o robô SIMULADO da doca
#   ./lab.sh <modo> teleop                   dirige pelo teclado (no robo, pede SIM)
#   ./lab.sh <modo> patrulha                 a nossa patrulha (validar_pontos antes; no robo, pede SIM)
#   ./lab.sh <modo> voltar-doca              pede à patrulha rodando que volte à doca e encerre (no robo, pede SIM)
#   ./lab.sh <modo> salvar [nome]            grava o mapa em workspace/mapas/ e confere
#   ./lab.sh <modo> estado | logs [serviço]  o que está rodando / últimas linhas do log
#   ./lab.sh <modo> parar                    desliga tudo do modo e devolve workspace/ ao usuário
#   ./lab.sh <modo> compose <args...>        qualquer comando do docker compose, no arquivo certo
#   ./lab.sh conferir <mapa.yaml>            confere um mapa salvo (sem ROS, sem Docker)
#
# Serviços: gazebo e leve (só sim), slam, localizacao, nav2, rviz, teleop, patrulha, undock (só
# sim), ferramentas. Variáveis: MAPA, CONFIG, SYNC, VEL, GIRO, NAV2_PARAMS, MEM_GAZEBO, MUNDO,
# ROBO_NS (namespace do robô real; padrão /robot1, ROBO_NS= vazio para nenhum).
# No modo robo, toda ação confere antes se as imagens são Humble, a distro do robô (SEG-01).
# Explicação: docs/tarefas/2026-11-16-compose-e-alvos.md,
# docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md e specs/migracao-humble/
set -euo pipefail
ESTE=$(readlink -f "$0")
cd "$(dirname "$ESTE")/../.."   # raiz do projeto (raiz do repositório)
# Pastas montadas nos containers: criadas aqui para não nascerem como root.
mkdir -p workspace/mapas workspace/logs

uso() { sed -n 2,23p "$ESTE"; }

if [ "${1:-}" = conferir ]; then
  [ -n "${2:-}" ] || { echo "Uso: ./lab.sh conferir <mapa.yaml>"; exit 1; }
  PYTHONPATH="workspace/meu_ws/src/patrulha_tb4${PYTHONPATH:+:$PYTHONPATH}" \
    exec python3 -m patrulha_tb4.mapa_slam "$2"
fi

MODO=${1:-}; ACAO=${2:-}
case "$MODO" in
  sim)  OUTRO=robo ;;
  robo) OUTRO=sim ;;
  *) uso; exit 1 ;;
esac
shift 2 2>/dev/null || shift $#
ARQ=infra/compose/$MODO.yaml
dc()        { docker compose -f "$ARQ" "$@"; }
rodando()   { [ -n "$(docker compose -f "infra/compose/$1.yaml" ps -q 2>/dev/null)" ]; }
# Roda um comando ROS num container de passagem do serviço ferramentas. O entrypoint da imagem
# já carregou o ROS.
ferramenta() { dc run --rm -T ferramentas bash -c "$1"; }

# SEG-01: o robô do lab é Humble, e nós de outra distro na rede dele já o derrubaram (16/11:
# o Humble lê mal a ParticipantEntitiesInfo do Jazzy e o serviço turtlebot4 morre sem memória).
# Antes de qualquer container do modo robo, confere a distro gravada em cada imagem do robo.yaml.
DISTRO_ESPERADA=humble   # a única distro escrita num script de host, além do PRE-02 (IMG-04)
distro_de() {
  docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" 2>/dev/null \
    | sed -n 's/^ROS_DISTRO=//p'
}
distro_ok() {
  local img distro ok=0
  for img in $(docker compose -f infra/compose/robo.yaml --profile '*' config --images | sort -u); do
    distro=$(distro_de "$img")
    if [ "$distro" != "$DISTRO_ESPERADA" ]; then
      echo "RECUSADO (SEG-01): a imagem $img tem ROS_DISTRO='${distro:-sem variável ou sem imagem}'."
      ok=1
    fi
  done
  if [ "$ok" != 0 ]; then
    echo "O robô é $DISTRO_ESPERADA. Outra distro na rede dele pode derrubá-lo (2026-11-16)."
    echo "Construa as imagens Humble: infra/docker/construir_imagem.sh base robo"
  fi
  return "$ok"
}

# O sim e o robo não rodam juntos: com os dois ligados, fica fácil mandar um comando para o
# robô errado no terminal errado. (A rede isolada e o domínio 42 do sim já separam os dois.)
exigir_sozinho() {
  if rodando "$OUTRO"; then
    echo "O modo $OUTRO está rodando. Desligue antes: ./lab.sh $OUTRO parar"; exit 1
  fi
}

# Com o Discovery Server, o DDS do robô anuncia TODOS os endereços dele: o do Wi-Fi, o do cabo
# (192.168.185.3) e o da USB com a Create 3 (192.168.186.x). O PC responde em todos. Sem rota
# para esses dois pelo robô, as respostas saem pelo roteador, se perdem, e o PC nunca completa
# a descoberta (medido em 2026-11-16 com tcpdump: 545 pacotes para cada um, 33 para o Wi-Fi).
# O manual pede a rota da 192.168.186.0/24 pelo IP do robô (setup/discovery_server.html).
checar_rotas() {
  local ip rota dev con faltam=""
  ip=$(sed -nE 's/^ROS_DISCOVERY_SERVER=;*([0-9.]+):.*/\1/p' infra/lab/rede_lab.env)
  [ -n "$ip" ] || return 0   # Simple Discovery: não há servidor nem rota a conferir
  for alvo in 192.168.186.2 192.168.185.3; do
    rota=$(ip route get "$alvo" 2>/dev/null || true)
    # Ligado direto (o cabo na enp86s0, sem "via") ou pelo robô: ok. Pelo roteador: falta.
    if grep -q " via " <<<"$rota" && ! grep -q " via $ip " <<<"$rota"; then
      faltam+=" ${alvo%.*}.0/24"
    fi
  done
  [ -n "$faltam" ] || return 0
  dev=$(ip route get "$ip" 2>/dev/null | grep -oE 'dev [^ ]+' | cut -d' ' -f2)
  con=$(nmcli -g GENERAL.CONNECTION device show "$dev" 2>/dev/null || echo '<nome do Wi-Fi>')
  echo "REDE REPROVADA: o PC não tem rota pelo robô ($ip) para:$faltam."
  echo "O DDS do robô anuncia esses endereços, e sem a rota o PC não completa a descoberta."
  echo "Rode uma vez (fica salvo na conexão $con; explicação em docs/acesso-ao-robo-por-cabo.md):"
  echo "  sudo nmcli connection modify \"$con\" +ipv4.routes \"192.168.186.0/24 $ip 500, 192.168.185.0/24 $ip 500\""
  echo "  sudo nmcli connection up \"$con\""
  return 2
}

checar_rede() {
  # Só leitura (manual, setup/simple_discovery.html: "ros2 topic list" no PC e no robô).
  # Junta 4 listagens com 4 s entre elas: pelo Discovery Server, a descoberta leva alguns
  # segundos (no próprio robô, cerca de 10 s até os 31 tópicos aparecerem).
  local ns=${ROBO_NS-/robot1} topicos erro faltando=""
  checar_rotas || return 2
  erro=$(mktemp)
  # Se o container nem sobe (imagem faltando, Docker sem permissão), o erro aparece aqui, e
  # não disfarçado de "rede reprovada".
  if ! topicos=$(ferramenta 'for i in 1 2 3 4; do ros2 topic list; sleep 4; done | sort -u' 2>"$erro"); then
    echo "O container de teste não rodou:"; tail -3 "$erro"; rm -f "$erro"; return 2
  fi
  rm -f "$erro"
  for t in scan tf odom; do grep -qx "$ns/$t" <<<"$topicos" || faltando+=" $ns/$t"; done
  for t in battery_state dock_status; do   # a patrulha precisa; o SLAM não
    grep -qx "$ns/$t" <<<"$topicos" && echo "  ok   $ns/$t" || echo "  aviso: $ns/$t não apareceu (a patrulha vai precisar)"
  done
  if [ -n "$faltando" ]; then
    echo "REDE REPROVADA: faltam$faltando. Confira ROS_DOMAIN_ID, RMW e o discovery em infra/lab/rede_lab.env,"
    echo "e o namespace do robô (ROBO_NS, hoje '${ns:-nenhum}')."
    return 2
  fi
  echo "REDE OK: $ns/scan, $ns/tf e $ns/odom do robô chegam ao PC."
}

liberar_tela() {
  [ -n "${DISPLAY:-}" ] || { echo "Sem DISPLAY: rode num terminal da área de trabalho."; exit 1; }
  xhost +SI:localuser:root >/dev/null   # o container roda como root
}

# SEG-01 vale para toda ação do modo robo. A exceção é o "parar", que com imagem errada só
# derruba o que estiver rodando (docker compose down) e não sobe o container de chown.
GUARDA_OK=1
if [ "$MODO" = robo ]; then
  if ! distro_ok; then
    GUARDA_OK=0
    [ "$ACAO" = parar ] || exit 1
  fi
fi

case "$ACAO" in
  subir)
    [ $# -gt 0 ] || { echo "Diga quais serviços. Ex.: ./lab.sh $MODO subir slam rviz"; exit 1; }
    for s in "$@"; do
      case "$s" in
        teleop|patrulha|undock) echo "$s é interativo: use ./lab.sh $MODO $s"; exit 1 ;;
        rviz) liberar_tela ;;
      esac
    done
    exigir_sozinho
    # No robô, nada sobe sem a rede funcionando: o erro aparece aqui, e não no meio do mapa.
    [ "$MODO" = robo ] && { checar_rede || { echo "Nada foi iniciado."; exit 1; }; }
    dc up -d "$@"
    echo "Subiu: $*. Acompanhe com ./lab.sh $MODO logs <serviço>."
    ;;
  checar-rede)
    [ "$MODO" = robo ] || { echo "checar-rede é só do modo robo."; exit 1; }
    checar_rede
    ;;
  teleop|patrulha|undock)
    [ "$ACAO" = undock ] && [ "$MODO" = robo ] && { echo "No robô real, o undock é à mão (kit de campo, etapa 3)."; exit 1; }
    exigir_sozinho
    dc run --rm "$ACAO"
    ;;
  voltar-doca)
    # PAT-23: só chama o serviço do nó da patrulha (um comando de CLI de uma resposta). Quem
    # decide e move o robô é a patrulha (decisao.py): cancela o destino, vai à doca, encaixa e
    # encerra com o código 0. Não envia dock nem undock por conta própria (SEG-06).
    ns=""; [ "$MODO" = robo ] && ns=${ROBO_NS-/robot1}
    if [ "$MODO" = robo ]; then
      echo "ATENÇÃO: a patrulha vai levar o robô REAL de volta à doca e encerrar."
      read -r -p 'Pessoa de segurança ao lado? Digite SIM para continuar: ' resposta
      [ "$resposta" = SIM ] || { echo "Cancelado."; exit 1; }
    fi
    # O timeout evita esperar para sempre se a patrulha não estiver rodando (o serviço não existe).
    ferramenta "timeout 30 ros2 service call ${ns}/patrulha/voltar_doca std_srvs/srv/Trigger" \
      || { echo "Sem resposta em 30 s: a patrulha está rodando em ./lab.sh $MODO patrulha?"; exit 1; }
    echo "Pedido enviado. Confirme o resultado no terminal da patrulha e em /dock_status."
    ;;
  salvar)
    [ -n "$(dc ps -q slam 2>/dev/null)" ] || { echo "O serviço slam não está rodando: ./lab.sh $MODO subir slam"; exit 1; }
    padrao=$([ "$MODO" = robo ] && echo lab || echo sim_maze)_$(date +%F_%H-%M)
    nome=${1:-$padrao}
    # Caracteres aceitos (herdado do regex do slam_toolbox; também mantém o nome seguro no shell).
    [[ "$nome" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Nome inválido: use só letras, números, _ . -"; exit 1; }
    [ ! -e "workspace/mapas/$nome.yaml" ] || { echo "Já existe workspace/mapas/$nome.yaml. Escolha outro nome."; exit 1; }
    read -r -p "O mapeamento começou com o robô encaixado na doca? [s/n] " doca
    case "$doca" in s|S) doca=sim ;; n|N) doca=nao ;; *) doca=nao_informado ;; esac
    # Chama o map_saver_cli direto, e não o serviço /slam_toolbox/save_map do manual. No robô real
    # o SLAM roda em /robot1: o serviço sem namespace não tem quem atenda (o comando trava) e o
    # /robot1/slam_toolbox/save_map responde result=255, porque o map_saver_cli que ele chama
    # assina /map e o mapa está em /robot1/map (medido em 2026-11-19). Aqui o remapeamento leva
    # o map_saver_cli ao tópico certo: ROBO_NS no modo robo; no sim o SLAM não usa namespace.
    # map_subscribe_transient_local: o /map do slam_toolbox é transient_local, e sem isso o
    # map_saver perde o mapa já publicado. Grava direto em /mapas (= workspace/mapas/).
    # O exec não passa pelo entrypoint: carrega o ROS pela ROS_DISTRO do próprio container.
    ns_mapa=""; [ "$MODO" = robo ] && ns_mapa=${ROBO_NS-/robot1}
    saida=$(timeout 60 docker compose -f "$ARQ" exec -T slam bash -c "source /opt/ros/\$ROS_DISTRO/setup.bash; \
      ros2 run nav2_map_server map_saver_cli -f '/mapas/$nome' --ros-args \
      -r map:=${ns_mapa}/map -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0" 2>&1 || true)
    if ! grep -q 'Map saved successfully' <<<"$saida" || [ ! -f "workspace/mapas/$nome.yaml" ]; then
      echo "$saida" | tail -5
      echo "FALHOU ao salvar. O SLAM já publicou ${ns_mapa}/map? Veja ./lab.sh $MODO logs slam"
      exit 1
    fi
    dc exec -T slam chown "$(id -u):$(id -g)" "/mapas/$nome.yaml" "/mapas/$nome.pgm"
    # Ficha do mapa: de onde ele veio, para saber depois qual versão e qual situação.
    versao=$(git rev-parse --short HEAD 2>/dev/null || echo sem_git)
    [ -n "$(git status --porcelain 2>/dev/null)" ] && versao+=" (com mudanças não commitadas)"
    cat > "workspace/mapas/$nome.info.txt" <<EOF
mapa: $nome
data: $(date '+%F %T %z')
modo: $MODO
comecou_na_doca: $doca
slam: turtlebot4_navigation slam.launch.py (sync=${SYNC:-true})
git: $versao
EOF
    echo "Salvo: workspace/mapas/$nome.yaml, .pgm e .info.txt"
    dc exec -T slam bash -c "cd /workspace/meu_ws/src/patrulha_tb4 && python3 -m patrulha_tb4.mapa_slam /mapas/$nome.yaml"
    ;;
  estado)
    dc ps
    ;;
  logs)
    dc logs --tail 40 "$@"
    ;;
  parar)
    # Devolve ao usuário o que os containers (root) gravaram nas pastas montadas.
    if [ "$GUARDA_OK" = 1 ]; then
      ferramenta "chown -R $(id -u):$(id -g) /workspace/mapas /workspace/logs" >/dev/null 2>&1 || true
    fi
    dc --profile '*' down
    xhost -SI:localuser:root >/dev/null 2>&1 || true
    echo "Parado (modo $MODO)."
    ;;
  compose)
    dc "$@"
    ;;
  *)
    uso; exit 1 ;;
esac

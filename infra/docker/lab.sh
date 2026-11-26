#!/usr/bin/env bash
# Atalho para os serviços do Docker Compose (infra/compose/sim.yaml e robo.yaml). Faz só o que
# o Compose não faz sozinho: conferir a rede, liberar a tela, salvar o mapa com a ficha e
# impedir o sim e o robo de rodarem juntos.
#
#   ./lab.sh <sim|robo> subir <serviço...>   sobe em segundo plano (ex.: subir gazebo slam rviz)
#   ./lab.sh robo checar-rede                só lê: rotas, e /scan, /tf e /odom do robô chegam ao PC?
#   ./lab.sh robo usar [nome]                escolhe o robô, ajusta as rotas do PC (sudo) e testa a rede
#   ./lab.sh sim undock                      tira o robô SIMULADO da doca
#   ./lab.sh <modo> teleop                   dirige pelo teclado (no robo, pede SIM)
#   ./lab.sh <modo> patrulha                 a nossa patrulha (validar_pontos antes; no robo, pede SIM)
#   ./lab.sh <modo> voltar-doca              pede à patrulha rodando que volte à doca e encerre (no robo, pede SIM)
#   ./lab.sh robo llm                        linguagem natural; PARKING_BRAKE=false MOVE o robô (pede SIM)
#   ./lab.sh robo falar                      terminal para enviar pedidos ao nó llm (Enter vazio: pare)
#   ./lab.sh <modo> salvar [nome]            grava o mapa em workspace/mapas/ e confere
#   ./lab.sh <modo> estado | logs [serviço]  o que está rodando / últimas linhas do log
#   ./lab.sh <modo> parar                    desliga tudo do modo e devolve workspace/ ao usuário
#   ./lab.sh <modo> compose <args...>        qualquer comando do docker compose, no arquivo certo
#   ./lab.sh conferir <mapa.yaml>            confere um mapa salvo (sem ROS, sem Docker)
#
# Serviços: gazebo e leve (só sim), slam, localizacao, nav2, rviz, teleop, patrulha, undock (só
# sim), llm e falar (só robo), ferramentas. Variáveis: MAPA, CONFIG, SYNC, VEL, GIRO, NAV2_PARAMS, MEM_GAZEBO, MUNDO,
# ROBO (qual robô real: perfil em infra/lab/robos/; sem ele, o do último "usar", ou robot1).
# ROBO_NS troca o namespace do perfil (ROBO_NS= vazio para nenhum). Um robô por vez neste PC.
# No modo robo, toda ação confere antes se as imagens são Humble, a distro do robô (SEG-01).
# Explicação: docs/tarefas/2026-11-16-compose-e-alvos.md,
# docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md e specs/migracao-humble/
set -euo pipefail
ESTE=$(readlink -f "$0")
cd "$(dirname "$ESTE")/../.."   # raiz do projeto (raiz do repositório)
# Pastas montadas nos containers: criadas aqui para não nascerem como root.
mkdir -p workspace/mapas workspace/logs

uso() { sed -n 2,27p "$ESTE"; }

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

# "usar <nome>" vale sobre o ROBO e o ROBO_NS herdados do terminal.
ROBO_DO_TERMINAL=${ROBO:-}
if [ "$MODO" = robo ] && [ "$ACAO" = usar ] && [ $# -gt 0 ]; then
  ROBO=$1; unset ROBO_NS
fi

if [ "$MODO" = robo ]; then
  # shellcheck source=../lab/robo_ativo.sh
  . infra/lab/robo_ativo.sh
  # No stderr, para não entrar na saída que outros scripts leem.
  echo "Robô: $ROBO (${ROBO_ENDERECO:-sem servidor de descoberta}, namespace ${ROBO_NS:-nenhum})" >&2
fi

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

# Os contêineres do modo robo têm o mesmo nome de projeto para qualquer robô. Com serviços de um
# robô no ar, uma ação para outro (um terminal sem o ROBO=...) é recusada. Contêiner sem o
# rótulo é anterior aos perfis, quando só havia o robot1.
exigir_mesmo_robo() {
  local no_ar
  no_ar=$(docker ps --filter label=com.docker.compose.project=tb4-robo \
            --format '{{.Label "tb4.robo"}}') || { echo "Não consegui consultar o Docker."; exit 1; }
  [ -n "$(docker ps -q --filter label=com.docker.compose.project=tb4-robo)" ] || return 0
  no_ar=$(sed 's/^$/robot1/' <<<"$no_ar" | grep -vx "$ROBO" | sort -u | tr '\n' ' ' || true)
  [ -z "$no_ar" ] || {
    echo "Há serviços de outro robô no ar (${no_ar% }), e você pediu $ROBO."
    echo "Use ROBO=${no_ar%% *} ou desligue antes: ./lab.sh robo parar"; exit 1
  }
}

# Com o Discovery Server, o DDS do robô anuncia TODOS os endereços dele: o do Wi-Fi, o do cabo
# (192.168.185.3) e o da USB com a Create 3 (192.168.186.x). O PC responde em todos. Sem rota
# para esses dois pelo robô, as respostas saem pelo roteador, se perdem, e o PC nunca completa
# a descoberta (medido em 2026-11-16 com tcpdump: 545 pacotes para cada um, 33 para o Wi-Fi).
# O manual pede a rota da 192.168.186.0/24 pelo IP do robô (setup/discovery_server.html).
checar_rotas() {
  local ip=$ROBO_ENDERECO rota via padrao dev con faltam="" antigas=""
  [ -n "$ip" ] || return 0   # Simple Discovery: não há servidor nem rota a conferir
  for alvo in 192.168.186.2 192.168.185.3; do
    rota=$(ip route get "$alvo" 2>/dev/null || true)
    # Ligado direto (o cabo na enp86s0, sem "via") ou pelo robô: ok. Pelo roteador: falta.
    if grep -q " via " <<<"$rota" && ! grep -q " via $ip " <<<"$rota"; then
      faltam+=" ${alvo%.*}.0/24"
      # Se o "via" não é o roteador padrão, é a rota de outro robô nesta mesma conexão.
      via=$(grep -oE ' via [0-9.]+' <<<"$rota" | awk '{print $2}')
      padrao=$(ip route show default | awk '{print $3}')
      grep -qx "$via" <<<"$padrao" || antigas+="${antigas:+, }${alvo%.*}.0/24 $via 500"
    fi
  done
  [ -n "$faltam" ] || return 0
  dev=$(ip route get "$ip" 2>/dev/null | grep -oE 'dev [^ ]+' | cut -d' ' -f2)
  con=$(nmcli -g GENERAL.CONNECTION device show "$dev" 2>/dev/null || echo '<nome do Wi-Fi>')
  echo "REDE REPROVADA: o PC não tem rota pelo robô ($ip) para:$faltam."
  echo "O DDS do robô anuncia esses endereços, e sem a rota o PC não completa a descoberta."
  echo "Rode uma vez (fica salvo na conexão $con; explicação em docs/guias/acesso-ao-robo.md):"
  if [ -n "$antigas" ]; then   # as duas rotas para a mesma sub-rede não podem conviver
    echo "  sudo nmcli connection modify \"$con\" -ipv4.routes \"$antigas\""
  fi
  echo "  sudo nmcli connection modify \"$con\" +ipv4.routes \"192.168.186.0/24 $ip 500, 192.168.185.0/24 $ip 500\""
  echo "  sudo nmcli connection up \"$con\""
  return 2
}

checar_rede() {
  # Só leitura (manual, setup/simple_discovery.html: "ros2 topic list" no PC e no robô).
  # Junta 4 listagens com 4 s entre elas: pelo Discovery Server, a descoberta leva alguns
  # segundos (no próprio robô, cerca de 10 s até os 31 tópicos aparecerem).
  local ns=$ROBO_NS topicos erro faltando=""
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
    echo "REDE REPROVADA: faltam$faltando. Confira ROS_DOMAIN_ID e o discovery em $ROBO_ENV,"
    echo "o RMW em infra/lab/rede_lab.env e o namespace do robô (hoje '${ns:-nenhum}')."
    return 2
  fi
  echo "REDE OK: $ns/scan, $ns/tf e $ns/odom do robô chegam ao PC."
}

# Aponta para o robô escolhido as rotas das sub-redes internas, na conexão em uso. Muda SÓ o PC.
# Confere tudo antes de pedir o sudo: com o robô fora de alcance, nada é alterado.
usar_robo() {
  local ip=$ROBO_ENDERECO rota dev con salvas rede nova remover="" incluir="" mudou=0 args=()
  if [ -n "$ip" ]; then
    rota=$(ip route get "$ip" 2>/dev/null || true)
    if [ -z "$rota" ] || grep -q ' via ' <<<"$rota"; then
      echo "$ROBO ($ip) não está na rede deste PC. Confira o Wi-Fi e o IP em $ROBO_ENV."
      echo "Nada foi alterado."; return 2
    fi
    ping -c 3 -W 2 "$ip" >/dev/null 2>&1 || {
      echo "$ROBO ($ip) não responde ao ping. Ele está ligado? O IP mudou ($ROBO_ENV)?"
      echo "Nada foi alterado."; return 2
    }
    dev=$(grep -oE 'dev [^ ]+' <<<"$rota" | cut -d' ' -f2)
    con=$(nmcli -g GENERAL.CONNECTION device show "$dev") && [ -n "$con" ] || {
      echo "Não achei a conexão do NetworkManager em $dev. Nada foi alterado."; return 2
    }
    # Uma rota salva por linha, no formato "destino próximo-salto métrica".
    salvas=$(nmcli -g ipv4.routes connection show "$con" | tr ',' '\n' | sed 's/^ *//; s/ *$//')
    for rede in 192.168.186.0/24 192.168.185.0/24; do
      nova="$rede $ip 500"
      grep -qxF "$nova" <<<"$salvas" || incluir+="${incluir:+, }$nova"
      while IFS= read -r rota; do   # a mesma sub-rede apontando para outro robô sai
        [[ "$rota" != "$rede "* ]] || [ "$rota" = "$nova" ] || remover+="${remover:+, }$rota"
      done <<<"$salvas"
    done
    [ -z "$remover" ] || args+=(-ipv4.routes "$remover")
    [ -z "$incluir" ] || args+=(+ipv4.routes "$incluir")
    if [ ${#args[@]} -gt 0 ]; then
      echo "Conexão $con, rotas a alterar no PC (pede a senha do sudo):"
      [ -z "$remover" ] || echo "  sai:   $remover"
      [ -z "$incluir" ] || echo "  entra: $incluir"
      sudo nmcli connection modify "$con" "${args[@]}"
      mudou=1
    fi
    # Reaplica sem desconectar o Wi-Fi (o SSH aberto sobrevive); se não der, reconecta.
    if [ "$mudou" = 1 ] || ! checar_rotas >/dev/null; then
      sudo nmcli device reapply "$dev" || sudo nmcli connection up "$con"
      sleep 2
    else
      echo "As rotas já apontam para $ROBO."
    fi
  fi
  echo "$ROBO" > infra/lab/robos/.atual
  echo "Robô em uso: $ROBO. Os próximos comandos valem para ele, sem precisar de ROBO=."
  if [ -n "$ROBO_DO_TERMINAL" ] && [ "$ROBO_DO_TERMINAL" != "$ROBO" ]; then
    echo "ATENÇÃO: este terminal tem ROBO=$ROBO_DO_TERMINAL, que continua valendo. Rode: unset ROBO"
  fi
  echo "Testando a rede (cerca de meio minuto)..."
  checar_rede
}

liberar_tela() {
  [ -n "${DISPLAY:-}" ] || { echo "Sem DISPLAY: rode num terminal da área de trabalho."; exit 1; }
  xhost +SI:localuser:root >/dev/null   # o container roda como root
}

# Um controlador por vez no robô: a linguagem natural e os programas que andam sozinhos não
# rodam juntos. Olha os contêineres pelo rótulo do Compose, o que inclui os de "compose run".
conteineres_robo() {
  docker ps --no-trunc --filter label=com.docker.compose.project=tb4-robo \
    --format '{{.Label "com.docker.compose.service"}}|{{.Command}}'
}
exigir_um_controlador() {
  local rodando_agora
  rodando_agora=$(conteineres_robo) || { echo "Não consegui consultar o Docker."; exit 1; }
  case "$1" in
    llm)
      if grep -q '^llm|' <<<"$rodando_agora"; then
        echo "O nó llm já está rodando. Encerre-o antes (Ctrl+C no terminal dele)."; exit 1
      fi
      if [ "${PARKING_BRAKE:-true}" != true ] &&
         grep -qE '^(teleop|patrulha)\||patrol_loop|loop\.py' <<<"$rodando_agora"; then
        echo "Há uma patrulha ou o controle manual rodando. Encerre antes de soltar o freio."; exit 1
      fi ;;
    teleop|patrulha)
      if grep -q '^llm|' <<<"$rodando_agora"; then
        echo "O nó llm está rodando e também comanda o robô. Encerre-o antes."; exit 1
      fi ;;
  esac
}

# SEG-01 vale para toda ação do modo robo. A exceção é o "parar", que com imagem errada só
# derruba o que estiver rodando (docker compose down) e não sobe o container de chown.
GUARDA_OK=1
if [ "$MODO" = robo ]; then
  if ! distro_ok; then
    GUARDA_OK=0
    [ "$ACAO" = parar ] || exit 1
  fi
  case "$ACAO" in parar|estado|logs) ;; *) exigir_mesmo_robo ;; esac
fi

case "$ACAO" in
  subir)
    [ $# -gt 0 ] || { echo "Diga quais serviços. Ex.: ./lab.sh $MODO subir slam rviz"; exit 1; }
    for s in "$@"; do
      case "$s" in
        teleop|patrulha|undock|llm|falar) echo "$s é interativo: use ./lab.sh $MODO $s"; exit 1 ;;
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
  usar)
    [ "$MODO" = robo ] || { echo "usar é só do modo robo."; exit 1; }
    if [ $# -eq 0 ]; then
      echo "Em uso: $ROBO. Perfis: $(cd infra/lab/robos && ls -- *.env | sed 's/\.env$//' | tr '\n' ' ')"
    else
      usar_robo
    fi
    ;;
  teleop|patrulha|undock|llm|falar)
    [ "$ACAO" = undock ] && [ "$MODO" = robo ] && { echo "No robô real, o undock é à mão (kit de campo, etapa 3)."; exit 1; }
    case "$ACAO" in llm|falar) [ "$MODO" = robo ] || { echo "$ACAO é só do modo robo."; exit 1; } ;; esac
    exigir_sozinho
    [ "$MODO" = robo ] && exigir_um_controlador "$ACAO"
    if [ "$ACAO" != llm ]; then
      dc run --rm "$ACAO"
    else
      # Fechar o terminal não encerra um "compose run": o cliente ignora o sinal, o contêiner
      # segue vivo e o robô, andando. Um vigia à parte (este script fica preso esperando o
      # cliente) para o nó se o terminal fechar ou o script morrer; o nó então cancela a meta.
      nome=tb4-robo-llm
      encerrar_llm() {
        if [ -n "$(docker ps -q --filter "name=^$nome\$")" ]; then
          docker stop -t 15 "$nome" >/dev/null 2>&1 || true
        fi
      }
      (
        trap 'encerrar_llm; exit 0' HUP TERM
        while kill -0 $$ 2>/dev/null; do sleep 1; done
        encerrar_llm
      ) </dev/null >/dev/null 2>&1 &
      vigia=$!
      trap 'encerrar_llm; kill "$vigia" 2>/dev/null || true' EXIT
      dc run --rm --name "$nome" llm
    fi
    ;;
  voltar-doca)
    # PAT-23: só chama o serviço do nó da patrulha (um comando de CLI de uma resposta). Quem
    # decide e move o robô é a patrulha (decisao.py): cancela o destino, vai à doca, encaixa e
    # encerra com o código 0. Não envia dock nem undock por conta própria (SEG-06).
    ns=""; [ "$MODO" = robo ] && ns=$ROBO_NS
    if [ "$MODO" = robo ]; then
      echo "ATENÇÃO: a patrulha vai levar o robô REAL ($ROBO) de volta à doca e encerrar."
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
    ns_mapa=""; [ "$MODO" = robo ] && ns_mapa=$ROBO_NS
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
robo: ${ROBO:-simulado}
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
    # Os contêineres de "compose run" (llm, patrulha, teleop, falar, ferramentas) não são
    # removidos pelo "down". Saem antes, com o Nav2 ainda no ar: o nó llm primeiro, para
    # conseguir cancelar a meta ativa; depois os demais, que também podem comandar o robô.
    filtro=(--filter "label=com.docker.compose.project=tb4-$MODO")
    ids=$(docker ps -q "${filtro[@]}" --filter label=com.docker.compose.service=llm)
    if [ -n "$ids" ]; then
      # shellcheck disable=SC2086
      docker stop -t 15 $ids >/dev/null && echo "Nó llm encerrado."
    fi
    ids=$(docker ps -q "${filtro[@]}" --filter label=com.docker.compose.oneoff=True)
    if [ -n "$ids" ]; then
      echo "Encerrando também: $(docker ps "${filtro[@]}" --filter label=com.docker.compose.oneoff=True \
        --format '{{.Label "com.docker.compose.service"}}' | sort -u | tr '\n' ' ')"
      # shellcheck disable=SC2086
      docker stop -t 15 $ids >/dev/null || true
    fi
    # Devolve ao usuário o que os containers (root) gravaram nas pastas montadas.
    if [ "$GUARDA_OK" = 1 ]; then
      ferramenta "chown -R $(id -u):$(id -g) /workspace/mapas /workspace/logs" >/dev/null 2>&1 || true
    fi
    dc --profile '*' down --remove-orphans   # sobras paradas de "compose run"
    xhost -SI:localuser:root >/dev/null 2>&1 || true
    echo "Parado (modo $MODO)."
    ;;
  compose)
    dc "$@"
    ;;
  *)
    uso; exit 1 ;;
esac

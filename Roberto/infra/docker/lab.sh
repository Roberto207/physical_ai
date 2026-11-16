#!/usr/bin/env bash
# Atalho para os serviços do Docker Compose (infra/compose/sim.yaml e robo.yaml). Faz só o que
# o Compose não faz sozinho: conferir a rede, liberar a tela, salvar o mapa com a ficha e
# impedir o sim e o robo de rodarem juntos.
#
#   ./lab.sh <sim|robo> subir <serviço...>   sobe em segundo plano (ex.: subir gazebo slam rviz)
#   ./lab.sh robo checar-rede                só lê: /scan, /tf e /odom do robô chegam ao PC?
#   ./lab.sh sim undock                      tira o robô SIMULADO da doca
#   ./lab.sh <modo> teleop                   dirige pelo teclado (no robo, pede SIM)
#   ./lab.sh <modo> patrulha                 a nossa patrulha (validar_pontos antes; no robo, pede SIM)
#   ./lab.sh <modo> salvar [nome]            grava o mapa em workspace/mapas/ e confere
#   ./lab.sh <modo> estado | logs [serviço]  o que está rodando / últimas linhas do log
#   ./lab.sh <modo> parar                    desliga tudo do modo e devolve workspace/ ao usuário
#   ./lab.sh <modo> compose <args...>        qualquer comando do docker compose, no arquivo certo
#   ./lab.sh conferir <mapa.yaml>            confere um mapa salvo (sem ROS, sem Docker)
#
# Serviços: gazebo (só sim), slam, localizacao, nav2, rviz, teleop, patrulha, undock (só sim),
# ferramentas. Variáveis: MAPA, CONFIG, SYNC, VEL, GIRO, STAMPED, NAV2_PARAMS, MEM_GAZEBO.
# Explicação: docs/tarefas/2026-11-16-compose-e-alvos.md
set -euo pipefail
ESTE=$(readlink -f "$0")
cd "$(dirname "$ESTE")/../.."   # raiz do projeto (pasta Roberto/)
# Pastas montadas nos containers: criadas aqui para não nascerem como root.
mkdir -p workspace/mapas workspace/logs

uso() { sed -n 2,19p "$ESTE"; }

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
# Roda um comando ROS num container de passagem do serviço ferramentas.
ferramenta() { dc run --rm -T ferramentas bash -c "source /opt/ros/jazzy/setup.bash; $1"; }

# O sim e o robo não rodam juntos: com os dois ligados, fica fácil mandar um comando para o
# robô errado no terminal errado. (A rede isolada e o domínio 42 do sim já separam os dois.)
exigir_sozinho() {
  if rodando "$OUTRO"; then
    echo "O modo $OUTRO está rodando. Desligue antes: ./lab.sh $OUTRO parar"; exit 1
  fi
}

checar_rede() {
  # Só leitura (manual, setup/simple_discovery.html: "ros2 topic list" no PC e no robô).
  # Junta 3 listagens com 3 s entre elas: a descoberta do DDS leva alguns segundos.
  local topicos faltando=""
  topicos=$(ferramenta 'for i in 1 2 3; do ros2 topic list; sleep 3; done | sort -u' 2>/dev/null || true)
  for t in /scan /tf /odom; do grep -qx "$t" <<<"$topicos" || faltando+=" $t"; done
  for t in /battery_state /dock_status; do   # a patrulha precisa; o SLAM não
    grep -qx "$t" <<<"$topicos" && echo "  ok   $t" || echo "  aviso: $t não apareceu (a patrulha vai precisar)"
  done
  if [ -n "$faltando" ]; then
    echo "REDE REPROVADA: faltam$faltando. Confira ROS_DOMAIN_ID, RMW e o discovery em infra/lab/rede_lab.env."
    return 2
  fi
  echo "REDE OK: /scan, /tf e /odom do robô chegam ao PC."
}

liberar_tela() {
  [ -n "${DISPLAY:-}" ] || { echo "Sem DISPLAY: rode num terminal da área de trabalho."; exit 1; }
  xhost +SI:localuser:root >/dev/null   # o container roda como root
}

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
  salvar)
    [ -n "$(dc ps -q slam 2>/dev/null)" ] || { echo "O serviço slam não está rodando: ./lab.sh $MODO subir slam"; exit 1; }
    padrao=$([ "$MODO" = robo ] && echo lab || echo sim_maze)_$(date +%F_%H-%M)
    nome=${1:-$padrao}
    # O slam_toolbox só aceita estes caracteres no nome (regex em src/map_saver.cpp).
    [[ "$nome" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Nome inválido: use só letras, números, _ . -"; exit 1; }
    [ ! -e "workspace/mapas/$nome.yaml" ] || { echo "Já existe workspace/mapas/$nome.yaml. Escolha outro nome."; exit 1; }
    read -r -p "O mapeamento começou com o robô encaixado na doca? [s/n] " doca
    case "$doca" in s|S) doca=sim ;; n|N) doca=nao ;; *) doca=nao_informado ;; esac
    # Serviço do manual. Com caminho absoluto, o slam_toolbox chama o map_saver_cli e grava
    # direto em /mapas (= workspace/mapas/). O serviço sempre responde; o resultado real é o
    # campo result (0 = sucesso).
    saida=$(dc exec -T slam bash -c "source /opt/ros/jazzy/setup.bash; ros2 service call \
      /slam_toolbox/save_map slam_toolbox/srv/SaveMap \"{name: {data: '/mapas/$nome'}}\"" 2>&1 || true)
    if ! grep -q 'result=0' <<<"$saida" || [ ! -f "workspace/mapas/$nome.yaml" ]; then
      echo "$saida" | tail -5
      echo "FALHOU ao salvar. O SLAM já publicou algum mapa? Veja ./lab.sh $MODO logs slam"
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
    ferramenta "chown -R $(id -u):$(id -g) /workspace/mapas /workspace/logs" >/dev/null 2>&1 || true
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

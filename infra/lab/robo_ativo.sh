# shellcheck shell=bash
# Escolha do robô real. Use com "source", a partir da raiz do repositório.
# Entrada: ROBO (nome de um arquivo em infra/lab/robos/, sem o .env). Sem ele vale o robô do
#          último "lab.sh robo usar" (infra/lab/robos/.atual, local), e depois o robot1.
# Saída:   ROBO e ROBO_NS exportados; ROBO_ENV (o perfil) e ROBO_ENDERECO (IP do robô).
# ROBO_NS já definido no terminal continua valendo sobre o do perfil (ROBO_NS= para nenhum).
ROBO=${ROBO:-$(cat infra/lab/robos/.atual 2>/dev/null || true)}
export ROBO=${ROBO:-robot1}
ROBO_ENV=infra/lab/robos/$ROBO.env
if [[ ! "$ROBO" =~ ^[A-Za-z0-9_-]+$ ]] || [ ! -f "$ROBO_ENV" ]; then
  echo "Robô desconhecido: '$ROBO'. Perfis em infra/lab/robos/:" \
    "$(cd infra/lab/robos && ls -- *.env | sed 's/\.env$//' | tr '\n' ' ')" >&2
  exit 1
fi
export ROBO_NS=${ROBO_NS-$(sed -n 's/^ROBO_NS=//p' "$ROBO_ENV")}
ROBO_ENDERECO=$(sed -nE 's/^ROS_DISCOVERY_SERVER=;*([0-9.]+):.*/\1/p' "$ROBO_ENV")

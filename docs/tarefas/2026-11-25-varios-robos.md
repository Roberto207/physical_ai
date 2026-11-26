# 2026-11-25: perfis para vários robôs

**Resposta direta:** o PC escolhe o robô pela variável `ROBO` (`robot1`, padrão, ou `robot3`). Antes, o IP, o id do servidor e o `/robot1` estavam fixos em vários arquivos. Nenhuma configuração dos robôs ou da rede do PC foi alterada.

## Dados lidos do segundo robô

O Roberto rodou no robô e colou a saída: `humble`, série `1000000044bad95f`, `ROBOT_NAMESPACE=/robot3`, `ROS_DOMAIN_ID=0`, `ROS_DISCOVERY_SERVER=";;;127.0.0.1:11811;"` (id 3), `rmw_fastrtps_cpp`, `wlan0` 192.168.68.53, `usb0` 192.168.186.3, `eth0` desligada.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `infra/lab/robos/robot1.env` e `robot3.env` | Novos: namespace, domínio e servidor de descoberta de cada robô |
| `infra/lab/rede_lab.env` | Só o comum: RMW e transporte UDPv4 |
| `infra/lab/robo_ativo.sh` | Novo: lê o perfil e exporta `ROBO`, `ROBO_NS` e o endereço |
| `infra/compose/robo.yaml` | Carrega o perfil, rotula os contêineres e mostra o robô antes do `SIM` |
| `infra/docker/lab.sh` | Mostra o robô, recusa misturar robôs, indica a remoção de rotas de outro robô e grava o robô na ficha do mapa |
| `workspace/meu_ws/src/patrulha_tb4/launch/nav2_inf.launch.py` | Remapeamento do laser pelo namespace, antes fixo em `/robot1` |
| `workspace/patrulha_oficial/rodar.sh` | Namespace do perfil |
| `.claude/skills/preflight-robo/` | Namespace e IP do perfil |

## Como foi verificado

- `bash -n` nos quatro scripts.
- `docker compose config` com `robot1` e `robot3`: variáveis e rótulo corretos.
- Nome de robô inexistente: recusado.
- Contêiner de teste rotulado `robot1`, sem rede: ação para `robot3` recusada, para `robot1` aceita.
- Rota de outro robô, com um `ip` simulado: o comando de remoção aparece.
- Remapeamentos do Nav2 avaliados na imagem `physical-ai:base` para `/robot1`, `/robot3` e sem namespace.
- `ROBO=robot3 infra/docker/lab.sh robo checar-rede`: reprovou por falta das rotas, o esperado.
- `python3 infra/ferramentas/checar_caminhos.py`: ok.

**Não verificado:** tópicos do `robot3` no PC, Nav2, patrulha, LLM e movimento em qualquer robô; o `robot1` depois da mudança (estava inacessível). `shellcheck` não está instalado.

## Limites

- Um robô por vez neste PC. Dois robôs no mesmo Wi-Fi disputam as rotas das sub-redes internas.
- Mapa e pontos da patrulha são compartilhados. A doca do `robot3` não foi medida.
- `infra/compose/llm.yaml` (ensaio isolado) continua com `/robot1` por padrão.

## Efeito prático

Falta adicionar as rotas do `robot3` no PC e rodar `ROBO=robot3 infra/docker/lab.sh robo checar-rede` até dar `REDE OK`.

## Acréscimo: `lab.sh robo usar`

Depois do registro acima, o Roberto aplicou as rotas do `robot3` e o `checar-rede` deu `REDE OK`, com bateria e doca (saída colada por ele). Isso encerra o passo que faltava.

`infra/docker/lab.sh robo usar <nome>` confere se o robô responde na rede do PC, troca na conexão em uso as rotas das duas sub-redes internas, reaplica com `nmcli device reapply` (ou reconecta, se falhar), grava a escolha em um arquivo local ignorado pelo git e roda o `checar-rede`. O `infra/lab/robo_ativo.sh` lê a escolha quando `ROBO` não está definido.

Verificado:

- No PC, com as rotas já corretas, `usar robot3`: sem `sudo`, `REDE OK`.
- `usar robot1`, fora desta rede, e nome inexistente: recusados, sem alterar rotas.
- Troca de rotas e `sudo` recusado, com `ip`, `nmcli` e `sudo` simulados: comandos esperados; na recusa, a escolha não muda.
- Remoção e inclusão no mesmo `nmcli connection modify`, em modo `--offline`.

**Não verificado:** a troca real entre dois robôs com `sudo`, o `nmcli device reapply` e a descoberta logo depois dele.

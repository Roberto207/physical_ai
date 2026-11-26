# Máquinas e papéis

Regra do projeto: **o PC do laboratório comanda o robô, o robô físico testa, o notebook do Roberto só roda os testes sem ROS** (`tests/`). Não há simulação até a task 2 (ADR-003).

| Máquina | Papel | O que roda |
|---|---|---|
| Notebook do Roberto | Edição, documentação e testes sem ROS | `python3 -m pytest tests`, `ruff`, `bash -n scripts/*.sh`. Nada pesado |
| PC do laboratório | Comando do robô real | A imagem `physical-ai` (`docker/Dockerfile`) e os `scripts/`: localização, Nav2, RViz, patrulha, LLM e SLAM. O Ollama roda no próprio PC |
| TurtleBot 4 do INF | Teste no hardware real | ROS 2 Humble no Raspberry Pi; o PC se conecta pela rede. Movimento só com permissão (`docs/contexto/AGENTES.md`, seção 1) |

## 1. Notebook do Roberto (verificado em 2026-11-05)

| Item | Valor |
|---|---|
| SO | Lux 2 (Bellatrix), base Debian trixie/sid. **Não é Ubuntu** |
| CPU | 12 threads (Intel Raptor Lake-P) |
| RAM | 7,4 GiB totais (só cerca de 1,9 GiB livres durante a análise, com o ambiente de trabalho aberto) |
| GPU | Intel UHD (integrada). **Sem NVIDIA/CUDA** |
| Disco | 467 GB, 387 GB livres |
| Docker | 29.9.2, Compose v5.6.1, usuário no grupo `docker` |
| Python | 3.13.3 |
| ROS | não instalado no host |

Consequências:

1. **O limite de 7,4 GiB vale só aqui.** Tudo que for pesado neste notebook roda em container com teto de memória (`docker run --memory=...`). Um `docker build` sem limite já saturou a RAM e travou a máquina.
2. Sem GPU NVIDIA: nada de Isaac Sim nem treino local pesado.
3. O ROS roda dentro de container Ubuntu 22.04 com Humble, e o Python 3.13 do host não interfere.
4. Medições da época do Jazzy (Gazebo a 5 a 18% do tempo real, 2,6 GiB com janela) estão na tag `task1-concluida`, em `docs/historico/resultados-jazzy.md`. Foram o motivo de o notebook deixar de simular.

## 2. PC do laboratório

- Comanda o robô real, com o projeto em `~/physical_ai`.
- Imagem `physical-ai` (ROS 2 Humble), construída com `docker build -t physical-ai docker/`. Até 26/11 eram `physical-ai:base`, `:robo` e `:sim`, que podem ser apagadas com `docker image rm`.
- O `python3` do sistema não tem `pytest` (25/11): os testes rodam no notebook e no CI.

## 3. Robô TurtleBot 4 e rede: `robot1` (conferido no robô em 2026-11-16)

| Item | Valor |
|---|---|
| Distro | ROS 2 Humble, Ubuntu 22.04. O PC precisa falar Humble com ele |
| Modo de descoberta | **Discovery Server**: o servidor roda no próprio robô (`fast-discovery-server -i 1 -p 11811`) |
| No PC | `ROS_DISCOVERY_SERVER=;<IP do robô>:11811;` (o `;` antes do IP põe o servidor na posição 1, que é o id) e `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`, em `scripts/env.sh`. O `ROS_SUPER_CLIENT=True` fica só no `scripts/ros.sh` e na listagem do `scripts/checar.sh` |
| `ROS_DOMAIN_ID` | 0 nos dois lados |
| Namespace | `/robot1` em todos os nós: `/robot1/scan`, `/robot1/battery_state`, `/robot1/dock_status` etc. Os scripts usam `/$ROBO` |
| `cmd_vel` | `geometry_msgs/msg/Twist`, sem carimbo de tempo |
| Endereços do robô | `eth0` 192.168.185.3 (cabo), `usb0` 192.168.186.3 (Create 3 em 192.168.186.2), `wlan0` 192.168.7.7 (Wi-Fi) |
| Rotas no PC | O PC precisa de rotas para `192.168.186.0/24` (Create 3) e `192.168.185.0/24` (cabo) **pelo IP do robô**. Sem elas a descoberta não termina e nenhum tópico aparece. `scripts/checar.sh` confere e mostra o comando (hipótese H1: no Humble talvez não sejam mais necessárias) |
| Acesso | Cabo (IP fixo `192.168.185.10` no PC, `ssh robo`) e Wi-Fi (`ssh robo-wifi`). Passos em `docs/guias/acesso-ao-robo.md` |

Detalhes e a medição que originou esses fatos: `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md`.

Itens em aberto: `docs/contexto/pendencias.md`.

### Segundo robô, `robot3` (conferido no robô em 2026-11-25)

Número de série `1000000044bad95f`. ROS 2 Humble, namespace `/robot3`, domínio 0, Discovery Server com id 3, FastDDS. `wlan0` 192.168.68.53 no Wi-Fi `Robotica_Deco`, `usb0` 192.168.186.3, `eth0` desligada na leitura. No PC: `ROBO=robot3` (`scripts/env.sh`). O número de série do primeiro robô (`robot1`) não foi anotado. Com as rotas no PC, a rede foi aprovada em 25/11. Em 26/11, o Roberto relatou o LLM funcionando no `robot3` (`docs/tarefas/2026-11-25-llm-robot3-correcoes.md`).

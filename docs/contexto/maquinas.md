# Máquinas e papéis

Regra do projeto (ADR-002): **o PC do laboratório simula, o robô físico testa, o notebook do Roberto só roda o L0** (Python puro, sem ROS, sem simulador).

| Máquina | Papel | O que roda |
|---|---|---|
| Notebook do Roberto | Edição, documentação e testes L0 | `pytest` dos pacotes, checadores, `ruff`, `docker compose config`. Nada pesado |
| PC do laboratório (Gazebo) | Simulação principal | Gazebo Fortress sem janela, Nav2, SLAM e o L1 de injeção de falhas, pelas imagens `physical-ai:<alvo>` e o `lab.sh` |
| TurtleBot 4 do INF | Teste no hardware real | ROS 2 Humble no Raspberry Pi; o PC se conecta pela rede. **Não usar o `lab.sh robo` até a V5 da spec `specs/migracao-humble/`** |

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
4. Medições da época do Jazzy (Gazebo a 5 a 18% do tempo real, 2,6 GiB com janela) estão em `docs/historico/resultados-jazzy.md`. Foram o motivo de o notebook deixar de simular.

## 2. PC do laboratório

- Roda as imagens Humble `physical-ai:base`, `physical-ai:robo` e `physical-ai:sim`, construídas por `infra/docker/construir_imagem.sh`.
- Imagens de 2026-11-16 (Jazzy): `physical-ai:robo` 5,37 GB e `physical-ai:sim` 5,81 GB. A migração para Humble está commitada (F0 a F4), e falta rodar a V1, o teste de fumaça do Gazebo, a V3 e os 11 cenários L1 nesse PC.
- O `lab.sh` recusa imagem de outra distro (SEG-01).

## 3. Robô TurtleBot 4 e rede (conferido no robô em 2026-11-16)

| Item | Valor |
|---|---|
| Distro | ROS 2 Humble, Ubuntu 22.04. O PC precisa falar Humble com ele |
| Modo de descoberta | **Discovery Server**: o servidor roda no próprio robô (`fast-discovery-server -i 1 -p 11811`) |
| No PC | `ROS_DISCOVERY_SERVER=;<IP do robô>:11811;` (o `;` antes do IP põe o servidor na posição 1, que é o id) e `ROS_SUPER_CLIENT=True`, em `infra/lab/rede_lab.env` |
| `ROS_DOMAIN_ID` | 0 nos dois lados |
| Namespace | `/robot1` em todos os nós: `/robot1/scan`, `/robot1/battery_state`, `/robot1/dock_status` etc. O compose usa `ROBO_NS` (padrão `/robot1`) |
| `cmd_vel` | `geometry_msgs/msg/Twist`, sem carimbo de tempo |
| Endereços do robô | `eth0` 192.168.185.3 (cabo), `usb0` 192.168.186.3 (Create 3 em 192.168.186.2), `wlan0` 192.168.7.7 (Wi-Fi) |
| Rotas no PC | O PC precisa de rotas para `192.168.186.0/24` (Create 3) e `192.168.185.0/24` (cabo) **pelo IP do robô**. Sem elas a descoberta não termina e nenhum tópico aparece. `lab.sh robo checar-rede` confere e mostra o comando |
| Acesso | Cabo (IP fixo `192.168.185.10` no PC, `ssh robo`) e Wi-Fi (`ssh robo-wifi`). Passos em `docs/guias/acesso-ao-robo.md` |

Detalhes e a medição que originou esses fatos: `docs/tarefas/2026-11-16-robo-real-rede-e-namespace.md` e `specs/patrol-inf/kit-de-campo.md` (etapa 1).

Em aberto: se o robô é Lite ou padrão (o log mostra `Device type: OAK-D-PRO`, a câmera do modelo padrão) e a reserva de DHCP do 192.168.7.7.

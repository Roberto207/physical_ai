# Máquina do Roberto (verificada em 2026-11-05)

| Item | Valor |
|---|---|
| SO | Lux 2 (Bellatrix), base Debian trixie/sid. **Não é Ubuntu** |
| CPU | 12 threads (Intel Raptor Lake-P) |
| RAM | 7,4 GiB totais (só cerca de 1,9 GiB livres durante a análise, com o ambiente de trabalho aberto) |
| GPU | Intel UHD (integrada). **Sem NVIDIA/CUDA** |
| Disco | 467 GB, 387 GB livres |
| Docker | 29.9.2, Compose v5.6.1, usuário no grupo `docker` |
| Python | 3.13.3 |
| ROS | não instalado |
| Virtualização | roda direto no hardware (sem VM) |

## Consequências

1. O ROS 2 Jazzy é suportado oficialmente no **Ubuntu 24.04**. Instalar nativo em Debian trixie é arriscado. O caminho natural é um **container Docker com Ubuntu 24.04 + Jazzy**, o que usa sua base em Docker.
2. A RAM é o maior limite. Gazebo + Nav2 + RViz2 juntos são pesados para 7,4 GiB. Será preciso testar e, se necessário, usar simulação sem interface gráfica ou mundos simples.
3. Sem GPU NVIDIA, isso exclui o Isaac Sim e treino local pesado. A simulação no Gazebo com renderização por CPU/Intel deve funcionar, mas devagar.
4. Interface gráfica (Gazebo/RViz) dentro do Docker exige repassar X11/Wayland e `/dev/dri` ao container. É preciso testar.
5. O Python 3.13 do host não é problema, pois o ROS 2 Jazzy usa o Python do Ubuntu 24.04 dentro do container.

## Decisão pendente

Confirmar com o coordenador a distro e a versão do ROS que a equipe vai padronizar (o colega Gabriel usa Ubuntu 24.04 + Jazzy).

# ADR-001: Todas as imagens do projeto em ROS 2 Humble

**Status:** Aceito em 2026-11-18 (portão da spec `specs/migracao-humble/`)
**Data:** 2026-11-18

## Contexto

O robô do laboratório roda Humble (Ubuntu 22.04), e o PC roda Jazzy. Em 2026-11-16, os nós Jazzy do PC derrubaram o serviço `turtlebot4` do robô: a mensagem `ParticipantEntitiesInfo` mudou de formato depois do Humble. O ROS 2 não garante comunicação entre distribuições diferentes.

## Decisão

As quatro imagens (`base`, `robo`, `sim`, `llm`) passam a partir de `ros:humble-ros-base`. O Jazzy fica preservado na tag git `jazzy-final` e nas imagens `physical-ai:jazzy-<alvo>` do PC do laboratório.

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| Só `robo` em Humble, `sim` em Jazzy | Duas distros mantidas, e os perfis e launches em dobro |
| Atualizar o robô para Jazzy | Decisão do INF, fora do nosso controle |

## Consequências

### Positivas

- PC e robô falam a mesma versão das mensagens internas.
- O L0 do CI roda só em Humble.

### Negativas

- O `nav2_loopback_sim` não tem release para Humble.
- O simulador passa a ser o Ignition Fortress.

### Mitigação

- Vendorizar o loopback (ADR-002).
- Guarda de distro no `lab.sh robo` (SEG-01).
- Voltar ao Jazzy: `git checkout jazzy-final` e `for a in base robo sim; do docker tag physical-ai:jazzy-$a physical-ai:$a; done`.

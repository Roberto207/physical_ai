# ADR-003: Sem simulação até a task 2

**Status:** Aceito em 2026-11-26 (portão da spec `specs/reformulacao-task1/`)
**Data:** 2026-11-26
**Substitui:** ADR-002

## Contexto

A simulação do repositório (Gazebo com o mundo maze, L1 com `nav2_loopback_sim`, `lab_tb4`) só servia à patrulha v1 (`patrulha_tb4`), que saiu. Não existe mundo do Gazebo igual ao `mapa_lab_novo`. A patrulha oficial e o LLM foram validados direto no robô.

## Decisão

Toda a simulação sai. Validar é feito com os testes da parte pura (`tests/`) e no robô real. A task 2 (três robôs) monta a simulação de novo, a partir do launch oficial de vários robôs (`turtlebot4_ignition_bringup` + `turtlebot4_spawn`).

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| Manter só o Gazebo | Teria de ser refeito para vários robôs |
| Manter o L1 | Testa a patrulha v1, que saiu |

## Consequências

### Positivas

- Menos 30 arquivos, um estágio de imagem e um job de CI.

### Negativas

- Mudança na patrulha ou no LLM só é testada com movimento no robô.

### Mitigação

- `patrulha.sh --verificar-localizacao` e `llm.sh` com freio conferem tudo sem mover.

# Próximos degraus da patrulha

Registrado em 2026-11-13, ao fim dos passos 1 a 6 da spec `../specs/patrol-inf/`.

## Resposta direta

O pacote `patrulha_tb4` está pronto para os próximos degraus. Os três dependem de um pedido ou de uma decisão do Roberto.

| Degrau | Situação | O que falta |
|---|---|---|
| **M-GZ e L3** (Gazebo `maze`) | O `workspace/meu_ws/src/patrulha_tb4/config/gazebo_maze.yaml` já existe e foi validado contra o mapa | Pedido explícito para rodar a medição M-GZ (`../specs/patrol-inf/DESIGN.md`, seção 3). Só depois dela vem o TST-08 |
| **L4** (robô do INF) | O roteiro é `../specs/patrol-inf/kit-de-campo.md` | **Antes da visita, decidir como o notebook fala com o robô:** o container atual usa a rede isolada do Docker, e isso nunca foi testado com um robô real |
| **Revisão do Roberto** | A tabela "Decisões que tomei onde a spec não dizia" está em `../docs/registro-de-mudancas.md`, na entrada de 12/nov | Ler e dizer quais decisões entram no `DEFINE.md` e no `DESIGN.md` |

## Onde está o resto

- O que foi medido até aqui: `testes.md`, seção 6.
- Cada mudança, com o objetivo: `../docs/registro-de-mudancas.md`.
- Pendências menores: `../contexto/pendencias.md`.

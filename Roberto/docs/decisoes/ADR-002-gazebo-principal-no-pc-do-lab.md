# ADR-002: Gazebo no PC do laboratório como simulador principal

**Status:** Aceito em 2026-11-18 (portão da spec `specs/migracao-humble/`)
**Data:** 2026-11-18
**Substitui:** a decisão de 2026-11-09, revista em 2026-11-10 (`contexto/projeto/decisoes.md`), que punha o simulador leve como principal

## Contexto

O leve era o principal porque o notebook (7,4 GiB) não aguentava o Gazebo. Agora o PC do laboratório simula e o robô físico testa. O leve só exercita a lógica: a bateria, a doca e o AMCL são falsos.

## Decisão

O Ignition Fortress sem janela, no PC do laboratório, é o simulador principal (L3). O `nav2_loopback_sim` é vendorizado do ramo `jazzy` e continua como L1, para injetar falhas (dock, bateria, servidor).

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| L1 só com o Gazebo | Perde a injeção rápida de falhas dos 11 cenários |
| L1 numa imagem Jazzy isolada | Contradiz o ADR-001 |

## Consequências

### Positivas

- Doca, bateria e AMCL reais da simulação no teste principal.

### Negativas

- Cenários mais lentos (fator de tempo real não medido no PC).
- Um pacote de terceiros para manter.

### Mitigação

- A medição M-GZH no PC, só por pedido do Roberto.
- Um `ORIGEM.md` com o SHA do upstream e os patches.

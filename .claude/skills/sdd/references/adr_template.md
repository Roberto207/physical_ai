# Template de ADR (Architecture Decision Record)

Use para decisões arquiteturais caras ou difíceis de reverter, não para bugs ou ajustes
pequenos (isso é a trilha leve). Neste projeto os ADRs ficam em `docs/decisoes/`.

## Template completo

```markdown
# ADR-NNN: <título curto e específico>

**Status:** Proposto | Aceito | Substituído por ADR-XXX
**Data:** <AAAA-MM-DD>

## Contexto

<Qual problema motivou esta decisão? Cite a documentação oficial ou a medição que
sustenta a escolha, em vez de "porque é melhor".>

## Decisão

<Numerado, concreto, cita módulos/nomes de arquivo reais quando aplicável.>
1. ...
2. ...

## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| ... | ... |
| ... | ... |

## Consequências

### Positivas
- ...

### Negativas
- ...

### Mitigação
- ...
```

## Regras duras

- **Máximo 200 palavras por ADR.** Se você precisar de mais, é sinal de que são duas
  decisões acopladas — divida em ADR-NNN e ADR-NNN+1, e referencie um no outro.
- **Nunca pule "Alternativas Consideradas".** Um ADR sem alternativas rejeitadas não é
  uma decisão registrada, é uma opinião registrada — a tabela é o que prova que outras
  opções foram avaliadas de verdade, não descartadas por preguiça.
- **Escaneie a numeração antes de escrever.** `ls docs/decisoes/ADR-*.md`
  para não colidir com um ADR existente.
- Se uma decisão anterior é invalidada por esta, marque o ADR antigo como
  `Status: Substituído por ADR-NNN` — nunca delete um ADR histórico.

## Índice

Este projeto mantém o índice em `docs/decisoes/README.md`. Atualize-o na Fase 5.

## Exemplo de "Alternativas Consideradas" (formato)

```markdown
## Alternativas Consideradas

| Alternativa | Razão da rejeição |
|---|---|
| ROS 2 Jazzy nas imagens | O TurtleBot 4 do INF roda Humble, e o PC precisa falar a mesma distro |
| Gazebo com janela no notebook | Cerca de 18% do tempo real no melhor caso medido |
```

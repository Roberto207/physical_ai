# A escada básica: Zero-shot → Few-shot → CoT → Self-consistency

## Tabela de decisão (use a técnica mais barata que resolve)

| Técnica | Quando usar | Custo |
|---|---|---|
| **Zero-shot** | Tarefa simples, bem definida, o modelo já "sabe" o formato esperado | Mínimo |
| **Few-shot** | Formato específico, categorização com nuance, tom particular | Baixo (tokens dos exemplos) |
| **Chain-of-Thought (CoT)** | Raciocínio multi-passo, matemática, lógica, decisões com múltiplos fatores | Médio (tokens de raciocínio) |
| **Self-consistency** | CoT não é confiável o suficiente sozinho e o custo de rodar N vezes e votar compensa o ganho de acurácia | Alto (N× o custo de uma chamada CoT) |

Não pule direto para CoT ou self-consistency por padrão — comece pela técnica mais
simples que a tarefa exige e só suba na escada se os casos de teste (Fase 1 da skill)
mostrarem que é necessário.

## Zero-shot

Pede a tarefa direto, sem exemplos. Funciona bem quando a tarefa é comum o suficiente
para o modelo já ter um prior forte sobre o formato esperado (ex.: "resuma este texto
em 3 frases").

## Few-shot

Inclui exemplos de entrada→saída no próprio prompt. Boas práticas:

- **Cubra os casos-limite nos exemplos, não só o caso feliz.** Se a categoria "X" tem
  uma borda ambígua com "Y", um exemplo perto dessa borda vale mais que três exemplos
  óbvios.
- **Formato e delimitadores consistentes entre todos os exemplos.** Se um exemplo usa
  `###` e outro usa markdown, o modelo aprende a inconsistência, não o padrão.
- **Ordem: do mais simples para o mais complexo.** Exemplos complexos primeiro tendem a
  ancorar o modelo numa interpretação estreita da tarefa.
- **Sempre inclua pelo menos um exemplo negativo** quando a tarefa envolve
  classificação/decisão binária — mostrar só exemplos positivos deixa a fronteira da
  categoria subespecificada.

## Chain-of-Thought (CoT)

Pede para o modelo "pensar passo a passo" antes de responder — explicita o raciocínio
intermediário em vez de pular direto para a conclusão. Reduz erros em tarefas que têm
múltiplos passos de dependência lógica. Conecta-se ao padrão **ReAct**
(Reasoning+Acting) quando o raciocínio intercala com uso de ferramentas. Modelos Claude
4.x expõem isso nativamente via `thinking: {type: "adaptive"}` — nesses casos, o CoT
explícito no prompt é redundante, prefira o parâmetro do modelo.

## Self-consistency

Roda o mesmo prompt com CoT múltiplas vezes (temperatura > 0) e toma a resposta mais
frequente entre as execuções. Só vale o custo quando: (a) a tarefa é crítica o
suficiente para justificar N× o custo, e (b) o CoT sozinho já mostrou variância real
entre execuções nos seus casos de teste — não use como reflexo automático de "quero mais
confiança".

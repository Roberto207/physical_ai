# Padrões para prompts que controlam um sistema

Aplique os que fizerem sentido. Os exemplos são da integração de LLM no TurtleBot 4, em que
o modelo escolhe uma ação discreta e o código valida antes de executar.

## 1. Regras numeradas, cada uma ligada a uma falha

Numere as regras. Quando uma falhar num teste, dá para dizer qual. Uma regra sem um caso
de teste ou uma falha observada que a justifique deve sair.

## 2. Saída com schema fechado, e o cálculo no código

Peça um JSON com campos nomeados e valores de uma lista fechada. O que o modelo erra com
frequência (coordenadas, distâncias, limites) fica no código: o modelo escolhe o nome do
destino, e o código converte o nome em pose no mapa. Nunca execute código escrito pelo
modelo (`exec`).

## 3. Classificação: definição, exemplos e negação

Para cada ação permitida: uma definição de uma linha, 2 exemplos de pedidos que a pedem e
o caso de confusão negado de forma explícita.

```
Ação: <nome>
Definição: <uma linha>
Exemplos:
  - "<pedido 1>"
  - "<pedido 2>"
NÃO use esta ação quando: <caso de confusão>
```

## 4. Filtro determinístico antes e depois do modelo

Um comando de parada deve ser reconhecido por código, sem esperar o modelo. A resposta do
modelo passa por um validador antes de chegar ao robô. O código determinístico não muda
entre execuções e não é convencido por texto injetado no pedido.

## 5. Fail-closed quando há movimento

Resposta inválida, ação fora da lista, erro de rede ou demora acima do prazo: o robô não se
move. Decida isso explicitamente e escreva um teste para cada caso.

## 6. Exemplos positivos e negativos

Quando houver ambiguidade entre ações, inclua no prompt um exemplo certo e um errado.

## 7. Correção contra casos que falharam

Cada falha nova vira um caso de teste antes de o prompt ser alterado.

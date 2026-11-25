# Técnicas avançadas de raciocínio

Use só quando a escada básica (`tecnicas_ladder.md`) não for suficiente — cada uma
destas tem custo de tokens maior e complexidade de prompt maior, então precisa se
justificar pelos casos de teste da Fase 1, não por serem "mais sofisticadas".

## Tabela de decisão (gatilho de uso → técnica)

| Gatilho | Técnica |
|---|---|
| Tarefa tem um "estímulo" ou dica que ajuda a guiar o raciocínio sem ditar a resposta | Directional Stimulus Prompting |
| Erros comuns vêm de um raciocínio quase-certo que erra num detalhe sutil | Contrastive Chain-of-Thought |
| Tarefa se beneficia de múltiplos "especialistas" avaliando o mesmo problema de ângulos diferentes | Tree-of-Thought |
| Resposta é longa/estruturada e a qualidade cai quando gerada de uma vez só | Skeleton-of-Thought |
| Tarefa exige conhecimento de fundo que o modelo tem mas não ativa espontaneamente | Generated Knowledge Prompting |

## Directional Stimulus Prompting

Fornece uma pista/palavra-chave curta que direciona o raciocínio do modelo sem ditar a
resposta final — funciona como um "empurrão" em vez de uma instrução completa. Útil
quando você sabe qual ângulo do problema é relevante mas quer que o modelo desenvolva o
raciocínio.

## Contrastive Chain-of-Thought

Mostra, no few-shot, um exemplo de raciocínio **correto** lado a lado com um exemplo de
raciocínio **incorreto mas plausível** — o contraste ensina o modelo a reconhecer e
evitar o erro sutil, não só a replicar o padrão certo. Particularmente eficaz quando os
erros observados nos casos de teste não são aleatórios, mas seguem um padrão específico
de raciocínio quase-certo.

## Tree-of-Thought

O truque prático mais simples: peça ao modelo para simular **três especialistas**
avaliando o problema independentemente, cada um expondo seu raciocínio passo a passo, e
então convergir numa resposta considerando os três ângulos. Bom para decisões com
trade-offs genuínos onde uma única linha de raciocínio tende a ancorar cedo demais numa
resposta.

## Skeleton-of-Thought

Gera em duas fases: primeiro um **esqueleto** (a estrutura de tópicos da resposta, sem
desenvolver nenhum), depois preenche cada ponto do esqueleto. Reduz o problema de
respostas longas perderem coerência/qualidade ao longo da geração, e permite paralelizar
o preenchimento se a latência importar.

## Generated Knowledge Prompting

Antes de responder a pergunta principal, pede ao modelo para gerar fatos/conhecimento
relevante sobre o tópico primeiro, e só depois usar esse conhecimento gerado para
responder. Útil quando a tarefa depende de conhecimento de fundo que o modelo "sabe" mas
não ativa espontaneamente ao ir direto para a resposta — forçar a geração explícita do
conhecimento antes aumenta a chance de ele ser usado.

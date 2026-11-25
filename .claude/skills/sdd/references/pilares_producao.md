# Os 3 pilares de produção (e o anti-padrão que eles resolvem)

## O padrão 500/50/0

O sintoma clássico de "vibe coding" sem spec: o agente gera 500 linhas, você entende
umas 50, e em 3 meses ninguém consegue manter 0. Um agente que produz código que
*funciona* resolveu só uma fração pequena do problema real (a estimativa usual é ~25%). Os
outros ~75% são os três pilares abaixo, e é exatamente isso que a sub-fase **Design** (2c)
do pipeline completo deve cobrir explicitamente.

## Os 3 pilares

### 1. Identidade

O sistema sabe, de forma auditável, **quem** fez cada ação — qual usuário, qual agente,
qual versão do prompt/modelo. Sem identidade, um bug em produção não tem como ser
reproduzido nem atribuído. Pergunta de design: "se isso quebrar amanhã, dá pra saber
exatamente qual código/prompt/input gerou o problema?"

### 2. Observabilidade

O sistema expõe métricas e logs suficientes para responder "está funcionando?" sem
precisar ler o código-fonte. Na patrulha: o log do nó registra cada goal enviado ao Nav2,
o resultado devolvido e a carga da bateria no momento da decisão. Pergunta de design: "se
o robô parar no meio da rota, os logs dizem qual etapa falhou e por quê?"

### 3. Rastreabilidade

Cada resposta/decisão do sistema consegue apontar de volta para a evidência que a
gerou. Na integração com LLM: ficam registrados o pedido, a ação que o modelo escolheu e o
veredito do validador. De forma mais geral: cada decisão de arquitetura tem um ADR, e cada
comportamento tem um teste que o trava. Pergunta de design: "dá para provar por que o
robô fez isso, ou é uma caixa-preta que 'parece' certa?"

## Como usar isso no `DESIGN.md`

Não é um checklist burocrático de marcar 3 caixinhas — é uma lente. Para cada componente
novo do design, pergunte explicitamente: como este componente resolve (ou ignora)
Identidade, Observabilidade e Rastreabilidade? Se a resposta para algum pilar for "não
resolve", isso precisa estar declarado como débito técnico consciente no `DESIGN.md`,
não como uma lacuna silenciosa descoberta depois em produção.

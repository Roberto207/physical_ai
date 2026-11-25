# EARS — Easy Approach to Requirements Syntax

Usado na sub-fase **Define** do pipeline completo para escrever critérios de aceite que
são testáveis por construção — cada frase segue um dos 5 moldes abaixo, nunca prosa livre.
É o mesmo formalismo usado por ferramentas como Kiro (AWS) no `requirements.md`.

## Os 5 moldes

1. **Ubiquitous** (sempre vale, sem gatilho) —
   `O sistema DEVE <comportamento>.`
   *Ex.: O sistema DEVE registrar cada goal enviado ao Nav2 com o horário e o resultado.*

2. **Event-driven** (reage a um evento) —
   `QUANDO <evento> ENTÃO o sistema DEVE <comportamento>.`
   *Ex.: QUANDO a carga da bateria ficar abaixo do limite configurado ENTÃO o sistema DEVE
   cancelar a rota e enviar o robô à doca.*

3. **State-driven** (vale enquanto um estado persiste) —
   `ENQUANTO <estado> o sistema DEVE <comportamento>.`
   *Ex.: ENQUANTO o robô estiver na doca carregando o sistema DEVE recusar o início de uma
   nova volta.*

4. **Unwanted behavior** (o que o sistema NÃO deve fazer, com condição) —
   `SE <condição indesejada> ENTÃO o sistema NÃO DEVE <comportamento>.`
   *Ex.: SE a LLM devolver uma ação fora da lista permitida ENTÃO o sistema NÃO DEVE
   executar nenhum comando no robô.*

5. **Optional** (comportamento condicional a uma feature/flag) —
   `ONDE <feature/condição> o sistema DEVE <comportamento>.`
   *Ex.: ONDE o modo simulado estiver ativo o sistema DEVE usar a bateria simulada.*

## Por que isso importa

Um critério em prosa livre ("o robô deve voltar logo para a doca") não é testável. Um
critério em EARS ("QUANDO a volta à doca for pedida ENTÃO o sistema DEVE cancelar o goal
atual em até 2 s") vira um teste automático quase de graça. É o que separa `DEFINE.md` de
uma lista de desejos.

## Uso prático

- Cada linha do `DEFINE.md` deve caber em exatamente um dos 5 moldes.
- Se uma frase não cabe em nenhum, ou é um requisito de design disfarçado (fala de
  *como*, não de *o quê*) — mova para `DESIGN.md` — ou está vaga demais para ser um
  critério de aceite de verdade.
- O subagente `sdd-ears-critico` existe especificamente para pegar essas duas falhas
  antes do portão de aprovação.

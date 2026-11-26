---
name: economia-agentes
description: Use antes de delegar a subagentes ou de tarefas com pesquisa ampla, saída longa (logs, build, testes) ou várias etapas. Decide como executar (direto, 1 subagente ou paralelo), com qual agente, modelo e esforço, e escreve o briefing. Não use para perguntas pontuais nem edições pequenas.
---

# Economia de agentes

Objetivo: gastar o mínimo do limite do plano do Claude (janela de 5 h + limite semanal, compartilhados com o claude.ai). Esta skill decide COMO executar. Ela não cria hooks nem cron e não edita settings.

## Regra deste ambiente

Subagente só é criado quando o usuário pede (por exemplo, "rode avaliadores"). Sem o pedido,
execute direto e, se a delegação compensar, proponha em 1 linha e espere a resposta.

## Passo 0: é território de outra skill?

| Pedido | Indique |
|---|---|
| spec, ADR, requisitos | sdd |
| escrever ou testar prompt | prompt-engineering |
| settings.json, hooks, variáveis de ambiente, permissões | update-config |
| revisar o diff em busca de bugs | code-review |
| automação recorrente, cron, "rodar sozinho" | schedule ou loop |

Se o pedido cair aqui, diga em 1 linha qual skill usar e pare.

## Passo 1: recusar ou rebaixar

- Fable: fica fora do limite do Pro e roda só com créditos pagos. Use só com confirmação explícita do Roberto de que aceita pagar. Sem ela, use o modelo da tabela de roteamento.
- "Usa vários agentes" numa tarefa sem partes independentes: rebaixe para o ramo certo e diga o motivo em 1 linha. Multiagente só compensa com paralelismo real. Se ele insistir, obedeça.

## Passo 2: escolher o ramo (vale o primeiro que se aplicar)

1. **Direto** na conversa principal se a tarefa exige ida e volta, se as fases compartilham muito contexto, se a saída bruta esperada cabe em ~2 mil tokens, ou se ela toca o robô físico.
2. **1 subagente** se a tarefa gera saída longa que não vai ser relida (logs do Nav2, `docker build`, `colcon test`, varredura do repositório) e o trabalho é autocontido e volta como resumo.
3. **Paralelo** se há subtarefas que não dependem do resultado umas das outras: de 2 a 4 em pesquisa de documentação.
   - Fork (subagente que herda a conversa inteira) só quando a subtarefa precisa de todo o contexto E o modelo da sessão serve, porque o fork usa o mesmo modelo da sessão.
   - **Simulação nunca em paralelo.** Duas simulações com o mesmo `ROS_DOMAIN_ID` na mesma rede enxergam os nós e tópicos uma da outra, e o resultado das duas fica inválido.

## Passo 3: rotear

Leia `references/roteamento.md` para escolher agente, modelo e esforço. Passe `model` e `effort` na chamada do Agent quando forem diferentes do que o agente já tem. Nunca deixe varredura ou testes herdarem o Opus da sessão.

## Passo 4: orçamento

| Limite | Valor | Ao estourar |
|---|---|---|
| Subagentes por execução | 0 por padrão; até 4 em pesquisa; teto de 6 no total | Pare e peça confirmação antes do 7º |
| Profundidade | principal → subagente; subagente não chama subagente | Pare e devolva o resultado à conversa principal |
| Retorno de subagente | até ~1.500 tokens | Não repasse o conteúdo, só o caminho do arquivo; anote para revisar o briefing |

## Passo 5: briefing

Todo prompt de subagente segue `references/briefing.md`: entradas por caminho de arquivo, nunca texto colado.

## Robô físico

Subagente não executa comando que alcance o TurtleBot 4 (`ssh`, publicação em tópico, action, serviço, `scripts/*.sh`). Essas ações ficam na conversa principal, onde o Roberto autoriza cada uma (`docs/contexto/AGENTES.md`, seção 1). Todo briefing leva essa proibição no campo NÃO FAÇA.

Para avaliar código sem alcançar o robô: repositório só para leitura, scripts do subagente fora
do projeto e `docker run --network none`. Peça que informe o que não conseguiu verificar.

## Saída da skill

Antes de executar, mostre em até 5 linhas:

    RAMO: direto | 1 subagente | paralelo (N) | recusar/adiar | outra skill: X
    AGENTE(S): ...
    MODELO/ESFORÇO: ...
    ORÇAMENTO: N subagentes, profundidade P
    MOTIVO: 1 frase com o critério

Se o usuário já pediu subagentes, execute sem esperar resposta, exceto no ramo recusar/adiar ou
quando estourar o orçamento. Se não pediu, vale a regra do topo.

## Fora do escopo

- Editar agentes, settings.json, hooks ou variáveis de ambiente: só indique o update-config. Ex.: limite rígido de profundidade com `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`.
- Ao trocar de assunto numa sessão longa, sugira `/clear` (custo zero) em vez de `/compact`.

# Physical AI: patrulha e LLM no TurtleBot 4

Projeto AKCIT (INF-UFG) de Physical AI com gêmeos digitais. A equipe tem duas missões: **patrol control** (patrulha autônoma do TurtleBot 4 com recarga na doca) e **integração de uma LLM** ao robô. Tudo roda em ROS 2 Humble, em containers Docker.

## Papel de cada máquina

| Máquina | Papel |
|---|---|
| Notebook do Roberto | Edição, documentação e testes L0 (Python puro, sem ROS). Limite de 7,4 GiB de RAM |
| PC do laboratório | Simula (Gazebo Fortress sem janela, Nav2, L1 de injeção de falhas) |
| TurtleBot 4 do INF | Teste no hardware real, só com permissão (`docs/contexto/AGENTES.md`, seção 1) |

Detalhes, rede e endereços: `docs/contexto/maquinas.md`.

## Comece por aqui

1. **Rodar algo:** `docs/guias/como-rodar.md`.
2. **Regras para agentes de IA (leia antes de agir):** `docs/contexto/AGENTES.md`.
3. **O que está em aberto:** ainda não há um arquivo de pendências. Os itens abertos estão em `docs/contexto/maquinas.md` e em `docs/tarefas/`.

## Mapa das pastas

| Pasta | Pergunta que responde | Entrada |
|---|---|---|
| `docs/contexto/` | O que é o projeto, quem trabalha nele, em que máquinas, com que regras | `docs/contexto/projeto.md`, `docs/contexto/maquinas.md`, `docs/contexto/stack.md` |
| `docs/guias/` | Como fazer uma coisa agora (comandos) | `docs/guias/como-rodar.md`, `docs/guias/acesso-ao-robo.md` |
| `docs/decisoes/` | Por que é assim | `docs/decisoes/README.md` (índice dos ADRs e das decisões antigas) |
| `docs/tarefas/` | O que foi feito e quando, uma linha por tarefa | `docs/tarefas/README.md` |
| `docs/historico/` | Registros congelados da época do Jazzy | `docs/historico/resultados-jazzy.md`, `docs/historico/registro-de-mudancas.md` |
| `specs/` | O que o sistema precisa fazer e como foi desenhado | `specs/patrol-inf/`, `specs/migracao-humble/`, `specs/enxugamento/` |
| `infra/` | Compose, imagens Docker, scripts do PC do lab e rede | `infra/docker/`, `infra/compose/`, `infra/lab/` |
| `workspace/` | Código: pacotes ROS (`meu_ws/`), mapas, o validador de ações da LLM (`exemplos/`) e logs (fora do git) | `workspace/meu_ws/src/patrulha_tb4`, `workspace/meu_ws/src/lab_tb4` |

## Níveis de teste

| Nível | O que prova | Onde roda |
|---|---|---|
| L0 | A lógica em Python puro (`pytest`) | Notebook e CI |
| L1 | O nosso nó com o Nav2 de verdade, com base, bateria e AMCL falsos (`infra/docker/teste_l1.sh`) | PC do lab |
| Gazebo | Doca, bateria e AMCL simulados | PC do lab |
| Robô | O hardware real | INF, com permissão |

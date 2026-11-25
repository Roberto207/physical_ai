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

| Quero | Arquivo |
|---|---|
| Rodar a patrulha que termina na doca | `docs/guias/patrulha-volta-a-doca.md` |
| Rodar a patrulha em loop contínuo | `docs/guias/patrulha-loop-continuo.md` |
| Lembrar um comando | `docs/guias/comandos-basicos.md` |
| Todo o resto (testes, imagens, simulador, mapa) | `docs/guias/como-rodar.md` |
| Trabalhar na integração com LLM | `workspace/llm/README.md` |
| Saber o que está em aberto | `docs/contexto/pendencias.md` |
| Regras para agentes de IA (leia antes de agir) | `docs/contexto/AGENTES.md` |

## Mapa das pastas

```text
physical_ai/
├── docs/
│   ├── contexto/     projeto, máquinas e rede, stack, regras, pendências
│   ├── guias/        como fazer agora (comandos)
│   ├── decisoes/     por que é assim (ADRs)
│   ├── tarefas/      o que foi feito, uma tarefa por arquivo
│   └── historico/    registros antigos, não atualizados
├── specs/            requisitos e desenho (ver specs/README.md)
├── infra/
│   ├── compose/      serviços do robô (robo.yaml) e do simulador (sim.yaml)
│   ├── docker/       imagens, lab.sh e teste_l1.sh
│   ├── lab/          rede do PC com o robô (rede_lab.env)
│   └── ferramentas/  checador de caminhos dos documentos
└── workspace/
    ├── patrulha_oficial/   patrulha em uso no robô
    ├── llm/                integração com LLM
    ├── mapas/              mapa em uso e pontos
    ├── meu_ws/src/         pacotes ROS: patrulha_tb4, lab_tb4, terceiros
    └── logs/               saídas das execuções (fora do git)
```

## Níveis de teste

| Nível | O que prova | Onde roda |
|---|---|---|
| L0 | A lógica em Python puro (`pytest`) | Notebook e CI |
| L1 | O nosso nó com o Nav2 de verdade, com base, bateria e AMCL falsos (`infra/docker/teste_l1.sh`) | PC do lab |
| Gazebo | Doca, bateria e AMCL simulados | PC do lab |
| Robô | O hardware real | INF, com permissão |

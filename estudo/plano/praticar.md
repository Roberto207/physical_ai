# Como praticar sem ter o robô na mão

## Resposta direta

**Você consegue praticar quase tudo no seu notebook, e a GPU remota quase não ajuda.** O que falta ao notebook é força para simular câmera e física. Mas a maior parte do seu trabalho nas missões é lógica em Python, que não precisa disso. Use o ambiente mais simples que responde à pergunta do momento.

Pense em aprender a dirigir: primeiro as regras, depois o simulador, depois o carro. Não se treina baliza numa rodovia.

## A escada de ambientes

| Degrau | Ambiente | Serve para | RAM medida | Situação |
|---|---|---|---|---|
| 1 | `pytest` sem ROS | Lógica da patrulha e validador da LLM | desprezível | Testado: 19 testes passam |
| 2 | `turtlesim` | Aprender nodes, topics, services e actions | não medida, teto de 800 MiB no teste | Testado: topic e action funcionam |
| 3 | Treino leve (`nav2_loopback_sim` + base falsa) | Ver o `patrol_loop` e o Navigator em ação, usar a API | 0,5 GiB, ou 0,9 GiB com RViz | **Roda, mas a navegação está falhando. Ver abaixo** |
| 4 | Gazebo sem janela, com GPU Intel | Física e sensores simulados | 1,9 GiB | Roda a cerca de 18% do tempo real, sem Nav2. Não testei com Nav2 |
| 5 | Servidor do INF | Validação com Nav2 completo | ? | Depende de confirmação |
| 6 | Robô real | Validação final | | Depende de acesso |

## Como usar cada degrau

Todos os comandos partem da raiz do projeto, `~/dev/physical_ai`.

### Degrau 1: lógica pura

```bash
docker run --rm --memory=1g -v "$PWD/workspace:/workspace" physical-ai:jazzy \
  bash -c "cd /workspace/exemplos && python3 -B -m pytest -q -p no:cacheprovider"
```

### Degrau 2: terminal ROS e turtlesim

```bash
infra/docker/ros.sh          # abre um terminal. Rode em outra aba para abrir mais um
ros2 run turtlesim turtlesim_node
infra/docker/ros.sh parar    # no fim, libera a memória
```

A pasta `workspace/` do projeto aparece como `/workspace` no container. **Salve seu código lá:** o resto do container some ao parar.

### Degrau 3: treino leve

```bash
infra/docker/treino_leve.sh iniciar --rviz --patrulha
infra/docker/treino_leve.sh logs
infra/docker/treino_leve.sh terminal
infra/docker/treino_leve.sh parar
```

Para provocar bateria baixa, defina variáveis antes do comando:

```bash
BATERIA_INICIAL=0.35 DESCARGA=0.005 infra/docker/treino_leve.sh iniciar --patrulha
```

**O que esse simulador é:** o Nav2 é real, mas não há física nem sensores de verdade. A posição é calculada a partir da velocidade comandada. Base e bateria são falsas, escritas por mim em `infra/tools/fake_tb4_base.py`.

**O que ele não prova:** nada sobre o robô real, como docking, desvio de obstáculo inesperado ou duração da bateria.

### Problema em aberto no treino leve

O `patrol_loop` original roda, sai da base falsa e lê a bateria, mas **a navegação está lenta e falha**:

| Observado | Valor |
|---|---|
| Ida até `(-5, 1)` | Falhou depois de 209 s, com 14 erros `Failed to make progress` |
| Robô preso com velocidade zero | Perto de `(-0,5, 0)` |
| Em outra execução, no trecho seguinte | Andou cerca de 14 m em cerca de 3 minutos |

Descartei três causas: CPU (3 ou 8 núcleos dão o mesmo resultado), obstáculo no mapa (a área está livre) e camada do `costmap` (a `StaticLayer` da documentação não mudou nada). **A causa não foi encontrada.**

Consequência: use o degrau 3 para ver o fluxo, aprender a API e testar a lógica de decisão. Não use para concluir que a navegação funciona, e não perca horas tentando consertar. Também nunca vi o trecho de docking rodar nos meus testes, e essa é a primeira coisa a conferir na semana 4.

### Degrau 4: Gazebo sem janela

`infra/docker/run_sim_headless.sh` roda o modo só com CPU (cerca de 5%). O modo com GPU e os resultados estão em `contexto/infra/teste-simulacao-2026-11-05.md`. Com janela, ele estourou o limite de 2,5 GiB.

## Colab e Kaggle

Dá vontade de usar, mas **não servem bem para simular o robô**, e não testei ROS em nenhum dos dois.

| | Google Colab | Kaggle |
|---|---|---|
| Regras | O [FAQ](https://research.google.com/colaboratory/faq.html) proíbe em todos os runtimes gerenciados `connecting to remote proxies`. No gratuito, também `remote control such as SSH shells, remote desktops` e `bypassing the notebook UI to interact primarily via a web UI` | Não consegui ler a [documentação oficial](https://www.kaggle.com/docs/notebooks): a página veio vazia. Leia antes de usar |
| Tempo | Até 12 h no gratuito, com desconexão por ociosidade e limites não publicados | 30 h de GPU por semana e sessões de 12 h, **segundo fontes de terceiros**, que podem estar desatualizadas |
| Simular robô | Má ideia. Ver o simulador por túnel ou desktop remoto esbarra nas regras (leitura minha, não de um advogado) | Falta confirmar |
| Avaliar a LLM | **Bom uso**: tudo dentro do notebook, sem túnel | **Bom uso**, se as regras permitirem |

Além das regras, há um problema prático: você precisaria reinstalar o ROS a cada sessão, e o robô simulado não fala com o seu notebook sem um túnel.

**Onde a GPU remota compensa:** rodar um modelo aberto dentro do notebook sobre um conjunto de frases, e salvar as respostas para analisar. Sem ROS, sem robô, sem túnel. É a semana 5. Mesmo assim, uma API gratuita pode ser mais simples: decida lá.

**Alternativa a checar:** [The Construct](https://www.theconstruct.ai/) oferece ROS e Gazebo pelo navegador, com conta gratuita. Só achei informação antiga sobre os limites (10 horas de simulação por mês, num texto de 2015). Crie uma conta e veja se vale.

## Regras para o notebook não travar

- Use sempre os scripts acima: eles têm teto de memória. Se estourar, só o container morre.
- Nunca use `docker build` com o `infra/docker/Dockerfile`: não tem limite de memória.
- Antes de subir o Gazebo, feche o navegador.
- Terminou? `parar`. Um container esquecido continua consumindo.

## Efeito prático

Das 48 horas, a maior parte acontece nos degraus 1 a 3, que rodam no seu notebook hoje. Só a validação final depende do INF. Isso reduz o risco: o atraso no acesso ao INF atrapalha o final, mas não trava seu estudo.

# Semana 4: missão 1, nossa patrulha (8 horas)

## O que é esta semana

Escrever a nossa versão do `patrol_loop`: pontos vindos de um arquivo, bateria vigiada **durante** o trajeto e falhas tratadas.

## A ideia que economiza mais tempo: separar decisão de execução

Testar uma regra de bateria no simulador leva minutos, e cada caso precisa ser provocado. Separe em duas partes:

| Parte | Faz o quê | Como testar | Velocidade |
|---|---|---|---|
| **Decisão** | "Com bateria X, na situação Y, o que fazer?" Python puro | `pytest` | milissegundos |
| **Execução** | Chama o Navigator e lê os sensores | Simulador | minutos |

Um exemplo está pronto e testado em `workspace/exemplos/decisao_patrulha.py`. **Ela é um ponto de partida, não a solução:** ainda não trata falha de destino nem repetição.

## O que construir

| Item | Hoje, no `patrol_loop` | Na nossa versão |
|---|---|---|
| Pontos | Fixos no código | Arquivo YAML |
| Bateria sem valor | Quebra | Aguarda |
| Bateria durante o trajeto | Não vê | Cancela e vai carregar |
| Destino que falhou | Só registra no log e segue | Conta, tenta de novo ou pula, com limite |
| Falha ao encaixar na base | Encerra | Tenta um número limitado de vezes, depois para e avisa |
| Por que decidiu algo | Pouco registro | Log claro de cada decisão |

## Como vigiar a bateria durante o trajeto

Use a diferença vista na semana 3: `goToPose` no lugar de `startToPose`. Esboço, **não testado**, para entender a forma:

```python
navigator.goToPose(destino)
while not navigator.isTaskComplete():
    if decidir(bateria_atual(), na_base=False) != 'patrulhar':
        navigator.cancelTask()
        break
    time.sleep(0.5)
resultado = navigator.getResult()   # TaskResult.SUCCEEDED, FAILED ou CANCELED
```

Para ler a bateria em paralelo, o `BatteryMonitor` do exemplo oficial, com a thread, já resolve.

## Passos (8 horas)

| Horas | O que fazer | Pronto quando |
|---|---|---|
| 1 | Rodar os testes de exemplo (`praticar.md`). Quebrar um número de propósito e ver o teste falhar | Você entende por que falhou |
| 2 | Ampliar a decisão: falhas de destino, tentativas de encaixe, e escrever os testes **antes** | Testes cobrem cada linha da tabela acima |
| 3 | Escrever o nó ROS: YAML, leitura da bateria, laço com `goToPose`, em `workspace/ros2_ws` | Roda no treino leve e o log faz sentido |
| 1 | Provocar as situações no treino leve: `DESCARGA` alta, `BATERIA_INICIAL` baixa | Viu o cancelamento e a ida à base |
| 1 | Escrever o README e guardar a saída dos testes | Um colega consegue rodar |

Para rodar seu nó com o simulador, suba o treino **sem** `--patrulha` e use `treino_leve.sh terminal`.

**Confira primeiro:** nos meus testes o caminho do docking nunca chegou a rodar. Se a base falsa (`infra/tools/fake_tb4_base.py`) der problema nele, me chame.

## Validar de verdade

O treino leve testa a sua lógica, mas não prova que o robô navega. Antes da entrega, rode no Gazebo completo do INF, com o comando do [manual](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html):

```bash
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py nav2:=true slam:=false localization:=true rviz:=true
```

Lá, a bateria e o dock vêm da simulação da Create 3, e não da minha base falsa. **Ainda não verifiquei isso:** no meu teste no Gazebo, nenhuma mensagem de `/battery_state` chegou em 8 a 10 s. Se a bateria não descarregar no simulador, publique um valor manualmente para testar. O manual também não deixa claro qual mundo cada exemplo espera: os pontos do `patrol_loop` usam `y = -23`, então confira no mapa.

## Entregável

Pacote `patrol_control` com o YAML de exemplo, testes passando, README e um log ou vídeo de uma volta com ida à base.

## Pronto quando

1. Testes passam para todas as linhas da tabela "O que construir".
2. No treino leve, o log mostra o robô abandonando um destino por bateria baixa e indo à base.

## Se travar

- Nav2 falha muito no treino leve: é o problema conhecido. Teste a decisão com `pytest` e siga em frente.
- Programa não termina: `isTaskComplete` precisa continuar sendo chamado no laço, pois é ele que processa a resposta do Nav2.
- Nav2 nunca fica pronto: no treino leve a base falsa precisa estar rodando, pois ela responde pelo AMCL.

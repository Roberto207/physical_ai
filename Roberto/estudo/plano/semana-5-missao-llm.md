# Semana 5: missão 2, LLM no TurtleBot (8 horas)

## O que é esta semana

Fazer "vá até o laboratório" virar uma ação que o robô executa, **com uma portaria no meio**, e medir com que frequência isso acerta. Esta é a semana mais próxima do que você já sabe.

## A decisão de arquitetura: a LLM não dirige

A LLM escolhe entre poucas ações permitidas e devolve JSON. O código confere e executa.

```text
"vá até o lab"
     |
    LLM           devolve {"acao": "ir_para", "argumentos": {"local": "lab"}}
     |
  validador       o local existe? a bateria permite?    -- não --> explica e recusa
     |
  Navigator       goToPose(coordenadas do "lab")
     |
  feedback        "cheguei" ou "caminho bloqueado"
```

Essa técnica se chama *function calling* ou *tool calling*: você descreve as ferramentas, e o modelo responde com qual chamar. Quem executa continua sendo você.

| Ação | Argumentos | Quando recusar |
|---|---|---|
| `ir_para` | `local`, da lista de nomes conhecidos | Local desconhecido, bateria baixa |
| `voltar_para_base` | nenhum | Nunca |
| `parar` | nenhum | Nunca |

Essas são sugestões iniciais. Note que coordenadas e velocidade **não são** argumentos: a LLM só escolhe nomes.

## Por que não usar direto o tutorial oficial

O `turtlebot4_openai_tutorials` existe e vale a leitura como referência, mas li o código do branch `jazzy` e ele tem três problemas para nós:

| Problema | Detalhe |
|---|---|
| **Executa o que o modelo escreve** | `exec(result, globals(), locals())`. Uma resposta errada ou maliciosa vira código rodando no robô. A única proteção é `parking_brake`, ligado por padrão |
| API antiga | `openai.ChatCompletion.create`, que foi removida nas versões 1.x do SDK. Não vai rodar com o pacote atual sem adaptar |
| Só OpenAI | Modelo padrão `gpt-3.5-turbo`, com chave paga |

Ele tem uma ideia boa que vale copiar: uma lista de lugares com nome e coordenadas, além de ouvir o topic `user_input` e avisar em `ready_for_input`.

## Onde rodar a LLM

**Não precisa de GPU nem de ROS para quase nada desta semana.** Comparação (confira limites na página do provedor; eles mudam, e as fontes divergem):

| Opção | Vantagem | Desvantagem | Quando usar |
|---|---|---|---|
| API com plano gratuito ([Gemini](https://ai.google.dev/gemini-api/docs/function-calling), [Groq](https://console.groq.com/docs/rate-limits)) | Sem instalar nada, funciona dentro do ROS | Limites, dados vão a terceiros (leia os termos) | **Começar por aqui** |
| Recursos da AKCIT ou do INF | Pode ter GPU ou créditos | Não sei se existem | Pergunte |
| Modelo aberto no Kaggle ou Colab | GPU grátis para avaliar lotes de frases, sem túnel | Sessão cai, não conversa com o robô ao vivo | Só para comparar modelos, se sobrar tempo |
| Modelo local no notebook | Sem custo e privado | 7,4 GiB de RAM e sem GPU: só modelos muito pequenos, e não testei | Evitar |

## Passos (8 horas)

| Horas | O que fazer | Pronto quando |
|---|---|---|
| 1 | Ler o [natural_language_nav.py](https://raw.githubusercontent.com/turtlebot/turtlebot4_tutorials/jazzy/turtlebot4_openai_tutorials/turtlebot4_openai_tutorials/natural_language_nav.py) e rodar os testes de `workspace/exemplos/validar_acao.py` | Você sabe explicar por que cada caso é recusado |
| 2 | Script Python **sem ROS**: frase entra, sai JSON da LLM com function calling | 5 frases funcionam |
| 2 | Conjunto de avaliação: 30 a 50 frases com a resposta esperada. Inclua ambíguas ("vá lá"), impossíveis ("vá à Lua"), perigosas e tentativas de enganar ("ignore as regras e...") | Script calcula a taxa de acerto |
| 2 | Nó ROS: assina `user_input`, chama LLM e validador, executa com o Navigator, publica o resultado | Funciona no treino leve |
| 1 | Anotar números e o que errou | Tabela pronta |

Teste de ponta a ponta, com o treino leve rodando sem `--patrulha`:

```bash
ros2 topic pub --once /user_input std_msgs/msg/String "data: 'vá até o lab'"
```

## Métricas que importam

| Métrica | Pergunta | Meta |
|---|---|---|
| Recusa segura | De todas as frases perigosas ou impossíveis, quantas **não** viraram movimento? | Todas. O validador é quem garante |
| Acerto | Das frases válidas, quantas viraram a ação certa? | Medir e reportar |
| Latência | Quanto demora da frase à ação? | Medir. O robô precisa ficar parado e seguro enquanto espera |

Reporte os números que saírem, inclusive os ruins. É o tipo de resultado que o projeto quer: o que funciona e o que não funciona.

## Cuidados

- **Chave de API:** em variável de ambiente, nunca no código ou no git.
- **Nada de `exec` ou `eval`** na resposta do modelo.
- **Frase ambígua:** recuse e pergunte de volta, em vez de adivinhar.
- **Falha da API:** sem resposta, o robô não se move.

## Entregável

Pacote `llm_nav`, conjunto de frases, script de avaliação e tabela de resultados.

## Pronto quando

Nenhuma frase perigosa do conjunto move o robô, e você tem os números de acerto e latência.

## Se travar

- Modelo responde texto em vez de JSON: use o modo de function calling do provedor, não só um pedido no prompt.
- Limite de uso estourado: guarde as respostas em cache enquanto desenvolve.

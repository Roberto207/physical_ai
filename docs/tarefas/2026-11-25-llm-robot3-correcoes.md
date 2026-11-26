# 2026-11-25: LLM no `robot3`, falhas encontradas e correções

**Resposta direta:** duas falhas do projeto foram corrigidas (o terminal `falar` e o tempo de espera da localização). O sistema **ainda não está pronto** no `robot3`: a base Create 3 saturou o processador com os serviços do PC no ar, e depois disso a odometria, a bateria e a doca deixaram de aparecer no PC.

## Falha 1: o terminal `falar` fechava ao enviar um pedido

- **Sintoma:** `UnicodeEncodeError: 'utf-8' codec can't encode character '\udcc3' in position 12: surrogates not allowed`. Com o terminal fechado, o operador perde o caminho do "pare".
- **Causa:** a linha digitada tinha um byte solto (`0xC3`, metade de uma letra acentuada). O Python o guarda como "surrogate", que o ROS não publica. O erro foi reproduzido em um contêiner sem rede. A origem provável do byte é o Backspace em um terminal sem `iutf8`, que apaga um byte e não a letra; isso não foi reproduzido com teclado.
- **Correção:** `workspace/meu_ws/src/llm_tb4/llm_tb4/entrada.py` descarta os bytes que não formam um caractere; o `falar.py` avisa e mostra o texto enviado. Linha que fica vazia vale como "pare". O serviço `falar` do `infra/compose/robo.yaml` passou a rodar `stty iutf8`.

## Falha 2: o AMCL era derrubado após 4 s sem sinal

- **Sintoma:** `CRITICAL FAILURE: SERVER amcl IS DOWN after not receiving a heartbeat for 4000 ms`.
- **Causa:** o `bond_timeout: 120.0` do `localization_inf.yaml` não chegava ao gerente de ciclo de vida, porque o `localization_launch.py` do Nav2 não lhe passa o arquivo de parâmetros.
- **Correção:** `workspace/meu_ws/src/patrulha_tb4/launch/localization_inf.launch.py` inclui o launch oficial e define o valor com `SetParameter`. O serviço `localizacao` passou a usá-lo.
- **Contrapartida:** um AMCL realmente parado passa a ser detectado em até 120 s. O nó LLM continua exigindo `map→odom` recente para mover.

## Falha 3, sem correção: a Create 3 satura

Lido no log da própria base (`http://<IP do robô>:8080/logs-raw`, só leitura), horários UTC:

| Situação | Processador da Create 3 (média) |
|---|---|
| Serviços do PC parados, períodos calmos | cerca de 45 a 60% |
| Localização, RViz, Nav2 e LLM no ar (21:51 a 22:03) | 100% |
| Um minuto depois de `lab.sh robo parar` | 49%, e 47 a 51% nos minutos seguintes |

A causa provável é o número de assinantes no PC dos tópicos da base, somado aos contêineres de diagnóstico; não foi isolado qual serviço pesa mais. Houve picos de 100% também em horários sem a pilha completa.

Depois da recuperação do processador, o PC via do robô apenas o `rplidar_composition` e o laser (cerca de 8 Hz). `odom`, `tf` da base, `dock_status` e `battery_state` não apareciam. Não se sabe se os programas pararam no robô ou se só não são descobertos. O `checar-rede` confere a lista de tópicos, e não se os dados chegam.

Na mesma sessão o Wi-Fi teve um pico de 1,3 s de latência com 27% de perda, que voltou ao normal sozinho; o RViz não explicou o pico.

## Ações no PC

O agente rodou `infra/docker/lab.sh robo parar`, o que encerrou o nó LLM que estava com o freio desligado. Nenhum comando de movimento foi enviado e nada foi alterado no robô.

## Verificação

- Testes do `llm_tb4` na imagem `physical-ai:base`: 238 passaram.
- `falar` de ponta a ponta em rede isolada: a linha com byte solto chegou ao tópico como "vá para a geladeira".
- Localização em rede isolada: `bond_timeout` 120.0 no gerente e `Managed nodes are active`.

**Não verificado:** as duas correções no robô, o `stty iutf8` com teclado, Nav2 e LLM no `robot3`.

## Efeito prático

Antes de subir os serviços, o robô precisa voltar a publicar `odom`, doca e bateria. Depois, subir um serviço por vez, acompanhando o processador da Create 3.

# 2026-11-22: análise do problema nomeado (por que a patrulha abortou no robô real)

**Resposta direta:** a causa mais provável dos abortos de 21/11 é a rede Wi-Fi entre o PC do laboratório e o robô, e não a lógica da patrulha. O dado novo que reforça isso: o colega que conseguiu rodar o `patrol_loop` oficial no mesmo robô estava ligado por **cabo Ethernet**, enquanto nós tentamos por Wi-Fi. **Isto é uma hipótese, não um diagnóstico**: ninguém mediu a rede no instante de uma falha, e o setup do colega não foi inspecionado.

## Contexto: por que existe uma v2

A patrulha própria (`patrulha_tb4`) fez o undock, mas o Nav2 abortou todos os destinos (`docs/tarefas/2026-11-21-novo-mapa-controle-ps4.md`). Cada correção (timeouts, `bond_timeout`, UDPv4, pose inicial, perfil do Nav2) deslocou o problema sem resolvê-lo. Um colega rodou o `patrol_loop` oficial do TurtleBot 4 no mesmo robô, seguindo só a documentação.

Para isolar a causa, abriu-se a branch `v2-patrol-oficial`, uma **v2 alternativa e estrita**: o `patrol_loop.py` oficial (ramo `humble` do `turtlebot4_tutorials`), com localização, Nav2 e RViz pelos launches oficiais, em Docker, e só os dados do nosso lab trocados (mapa, pose da doca, ponto de aproximação, pontos, namespace, rede). Sem `validar_pontos`, sem perfil de Nav2 nosso. A v1 em `main` não foi alterada. A spec e o estudo da v2 estão nessa branch, e não neste documento.

Esta análise foi feita antes de rodar a v2, a partir dos documentos já escritos, e muda como a v2 deve ser usada.

## Ponto 1: por que a rede é a causa mais provável

O Nav2 roda no PC e o robô fornece sensores e executa comandos. Scan, odometria, TF e `cmd_vel` atravessam a rede continuamente, e o controlador do Nav2 precisa de TF com poucas centenas de milissegundos de idade. Todos os sintomas registrados são de latência, nenhum é de lógica de patrulha:

| O que os logs mostraram | O que indica |
|---|---|
| `Transform data too old when converting from odom to map`, defasagem de cerca de 2,3 s | O TF `map→odom` chega atrasado ao PC |
| `map→odom` medido com 3,7 a 7,7 s de idade e depois com carimbo no futuro | Chegada intermitente, com filas, e não ausência permanente |
| `Controller patience exceeded` e `Unable to transform robot pose into global plan's frame` | O controlador desiste por falta de TF fresco |
| `compute_path_to_pose` com timeout e `async_send_request failed` no planejador | Chamadas de serviço e ação demoram além do prazo |
| `bond_timeout` abortando o lifecycle manager (4 s) e o AMCL levando cerca de 7 s para responder `get_state` | Descoberta e handshake do DDS lentos |
| `undock_falhou resultado=rejeitado` quando a confirmação só chegava depois dos 2 s | Resposta de ação tardia contada como rejeição |
| Ping PC→robô com 20 a 35% de perda e RTT médio de 793 a 1048 ms. O roteador também: 20% de perda e 355 a 425 ms | O problema já está no trecho PC↔ponto de acesso |

O undock funcionou e o Nav2 chegou a `Managed nodes are active`: o código e a configuração básica estão certos. A falha aparece quando o Nav2 precisa de tempo real. Cada correção anterior tratava um sintoma e melhorava só um pouco, o que é o padrão esperado quando o canal é instável.

## Ponto 2: o que o cabo muda e o que ele não prova

O cabo troca um canal com RTT de centenas de milissegundos e perda por um com RTT abaixo de 1 ms e sem perda. Isso explica por que o oficial funcionou para o colega. Mas mostra apenas que **o oficial funciona com cabo**, não que **o nosso código falha com cabo**. É possível que a v1 também funcione com cabo.

Outras causas que ainda podem existir:

| Hipótese | Por que ainda pode existir | Como separar |
|---|---|---|
| Relógios do PC e do Raspberry Pi fora de sincronia | `Transform data too old` e carimbos no futuro também aparecem com diferença de relógio, mesmo com cabo. O teste por SSH não foi feito por falta de senha | Comparar `date` nos dois lados, ou checar `chrony`/`timedatectl` |
| Mapa ruim: 59,8% desconhecido, "torto", doca fora da origem | O AMCL pode se perder e o planejador recusar metas | Alinhar o laser no RViz antes de cada rodada |
| A patrulha republica a `pose_inicial` a cada início | Pode sobrescrever a marcação manual do RViz | Remover a divergência (a v2 não tem esse mecanismo) |
| Parâmetros do Nav2 que alteramos | `bt_loop_duration` e timeouts que subimos | Usar o perfil oficial, como a v2 faz |

## Ponto 3: seguir exatamente a documentação ajuda?

Ajuda em parte, e por um motivo diferente do esperado.

- **Ajuda:** tira as nossas variáveis do caminho (nó próprio, perfil de Nav2, launch customizado, republicação de pose). Se a v2 funcionar com cabo, o ambiente está certo. Se falhar com cabo, a causa é outra (relógio ou mapa) e deixa de ser "nosso código".
- **Não ajuda sozinha:** sem o cabo, a v2 usa o mesmo Wi-Fi e deve repetir os abortos. Os timeouts oficiais do Nav2 (20 ms de `default_server_timeout`, 10 ms de `bt_loop_duration`) toleram menos latência que os nossos.
- **Custo:** a v2 perde o `validar_pontos`, o `voltar-doca` e o log estruturado da v1. É aceitável como teste, não como solução final.

## Ponto 4: o que muda no plano

1. **Medir antes de mover o robô, com o cabo:** ping (0% de perda e RTT bem abaixo de cerca de 50 ms), `ros2 topic hz /robot1/scan` e a idade do TF `map→odom`. Só leitura.
2. **Incluir a sincronia de relógio PC↔Pi** no portão de rede.
3. **Ajustar a rede da v2 ao cabo.** O arquivo de rede da v2 aponta hoje para o Wi-Fi (`;192.168.7.7:11811;`). Pelo `docs/contexto/maquinas.md`, no cabo o robô é `192.168.185.3` e o PC usa `192.168.185.10`, então a linha viraria `;192.168.185.3:11811;`. **Não verificado:** as rotas e o IP do PC em `docs/guias/acesso-ao-robo.md`, e se o servidor de descoberta atende também pela interface do cabo.
4. **Rodar a v2 como controle e depois a v1, ambas com cabo.** Se as duas funcionarem, a v1 volta a ser a base, com todas as vantagens dela. Se só a v2 funcionar, o problema está no nosso código.

## Não verificado

Qualquer medição de rede com cabo; a sincronia de relógio; o que exatamente o colega rodou (versão, parâmetros, mapa, onde ficou a doca); se a v1 funciona com cabo; a V5 da migração Humble.

## Efeito prático

O experimento mais informativo é o mesmo ensaio, com cabo, nas duas versões, depois de medir a rede e o relógio. Se a v1 passar com cabo, a v2 vira só referência e o trabalho que resta é garantir uma conexão estável (cabo, ou Wi-Fi bem medido). Até lá, não vale mexer mais no código da v1.

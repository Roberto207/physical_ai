# 2026-11-25: teste de localização e Nav2 dentro do `robot3`

**Resposta direta:** com os parâmetros do projeto, o Raspberry Pi do `robot3` ficou sobrecarregado ao subir o Nav2 junto com a localização. A navegação não deve migrar para o robô com base neste teste. Nenhum destino foi enviado.

## Objetivo

Saber se localização e Nav2 podem rodar no robô, por SSH, para não trocar as rotas do PC a cada robô.

## O que foi feito

O Roberto copiou o `mapa_lab_novo`, o `localization_inf.yaml` e o `nav2_inf_devagar.yaml` para a pasta teste_nav do usuário do robô e rodou os launches oficiais do `turtlebot4_navigation` (sem o `bond_timeout` do projeto). Os comandos foram executados por ele; o agente só leu as saídas coladas.

## Resultados

| Medida | Valor |
|---|---|
| Carga antes do teste (4 núcleos) | 1,20 |
| Carga ao entrar, com a localização e sem tópicos do Nav2 | 3,04 |
| Carga logo após interromper o Nav2 (1, 5 e 15 min) | 12,09 / 8,32 / 4,26 |
| Memória disponível na mesma leitura | 2,9 GiB de 3,7, sem swap |
| Laser antes de subir o Nav2 | cerca de 7,9 Hz |
| Descarte de leituras nos mapas de obstáculos | repetido por pelo menos 50 s; avisos 0,5 a 0,9 s após o horário da leitura |

No encerramento (`Ctrl+C`), cinco nós do Nav2 passaram por `Deactivating`; `waypoint_follower` e `velocity_smoother` não. Isso indica ativação incompleta.

## Não verificado

- Causa da carga: a lista de processos saiu cortada. A de 3,04 antes do Nav2 também não foi explicada.
- Se a carga baixaria com o Nav2 estabilizado, com a câmera desligada ou com frequências menores.
- Atraso de `scan` e `odom`: o `ros2 topic delay` não encontrou os tópicos em 15 s.
- Se o Nav2 foi iniciado com `ROS_SUPER_CLIENT=False`.
- Relógios do Raspberry Pi e da Create 3.

## Efeito prático

SSH serve para diagnóstico no robô. A navegação continua no PC, com os perfis de `2026-11-25-varios-robos.md`; as rotas do `robot3` foram aplicadas depois, com `REDE OK`.

# 2026-11-21: preparação da patrulha com mapa salvo

**Resposta direta:** o mapa `workspace/mapas/lab_teste.yaml` e sua imagem `workspace/mapas/lab_teste.pgm` estão presentes e o conferidor respondeu `UTILIZÁVEL`. A configuração `workspace/mapas/inf_lab_preenchido.yaml` foi **REPROVADA** pelo validador: `pose_inicial` em `(0,0)` está em célula desconhecida e `aproximacao_doca` em `(-0.6,0)` está fora do mapa. Os quatro pontos antigos passaram na validação geométrica. Não há base para iniciar o loop autônomo com essa configuração.

## Pipeline a executar no PC do laboratório

**Decisões do usuário:** registrar neste documento os resultados conforme cada etapa for executada; para movimento manual, usar o controle PS4 conectado ao TurtleBot 4 padrão. O serviço `teleop` por teclado não faz parte deste roteiro. Segundo o [manual oficial de condução](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/driving.html#joystick-teleoperation), o controle precisa estar pareado e conectado; a luz azul confirma a conexão. Segurar L1 ou R1 e mover o analógico esquerdo comanda o robô. Preferir L1 e deslocamentos curtos, com uma pessoa ao lado. Ainda não foi verificado nesta sessão se o controle conecta ou se o nó `joy_teleop` do robô está ativo.

1. Confirmar imagens Humble, rede ROS (`REDE OK`), ausência de simulador e containers anteriores parados. A sessão confirmou imagens Humble e `REDE OK` antes de `robo parar`; repetir a rede após a reinicialização dos serviços.
2. Abrir o mapa salvo com `MAPA=/mapas/lab_teste.yaml infra/docker/lab.sh robo subir localizacao nav2 rviz`, sem subir SLAM. No RViz, usar `2D Pose Estimate` na pose física da doca, conferir que laser e paredes coincidem e verificar se a área da doca é livre no mapa. Fonte oficial: [Navigation](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html).
3. Usar `Publish Point` para recolher coordenadas da doca, da aproximação e de cada destino. Registrar também orientações `yaw_graus` coerentes com a direção do robô; `Publish Point` fornece posição, não orientação. A aproximação deve permitir que o Create 3 detecte a doca energizada. Fonte oficial: [Docking](https://iroboteducation.github.io/create3_docs/api/docking/).
4. Criar uma configuração de **um ponto**, mantendo `mapa: lab_teste.yaml`, corrigindo `pose_inicial` e `aproximacao_doca`. Validar com `PYTHONPATH=workspace/meu_ws/src/patrulha_tb4 python3 -m patrulha_tb4.pontos workspace/mapas/<arquivo>.yaml`; exigir `APROVADA`. Se a doca estiver em área desconhecida, refazer o mapa começando nela antes da patrulha.
5. Com pessoa ao lado, área livre, doca energizada, bateria suficiente e Nav2 estável, rodar `CONFIG=/mapas/<arquivo>.yaml infra/docker/lab.sh robo patrulha`. O comando valida outra vez e pede `SIM` antes de mover. Acompanhar logs em `workspace/logs/`; `Ctrl+C` cancela a tarefa. Só ampliar para quatro pontos e para um ciclo de recarga após o teste de um ponto e nova validação. Fonte oficial do conceito: [TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html); implementação: `docs/guias/como_rodar_patrol_loop.md`.

## Verificação e limite

- `infra/docker/lab.sh conferir workspace/mapas/lab_teste.yaml`: `UTILIZÁVEL`, 11,00 m × 7,75 m; 42,7% não mapeado; origem do robô desconhecida na ficha do mapa.
- `PYTHONPATH=workspace/meu_ws/src/patrulha_tb4 python3 -m patrulha_tb4.pontos workspace/mapas/inf_lab_preenchido.yaml`: saída 2, duas poses inválidas; quatro destinos aprovados.
- Nenhum movimento foi comandado nem pontos novos recolhidos nesta tarefa. A validação V5 da migração Humble e o teste de docking real ainda não constam como aprovados nos documentos do projeto.

## Efeito prático

O mapa pode ser carregado para recolher pontos, mas a patrulha só pode começar depois que a doca for localizada e a configuração passar no validador.

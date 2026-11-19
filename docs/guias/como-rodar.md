# Como rodar

Desde 2026-11-18, tudo roda em **ROS 2 Humble**, a mesma distro do robô do laboratório (ADR-001, `docs/decisoes/`). O **PC do laboratório simula** e comanda o robô. O **notebook** só edita código e roda os testes L0. A versão Jazzy está na tag git `jazzy-final`.

Os caminhos abaixo partem da raiz do repositório. No notebook ela fica em `~/dev/physical_ai`; no PC do lab, em `~/physical_ai`.

## 1. Testes da lógica (L0): notebook ou PC, sem ROS e sem Docker

```bash
cd workspace/meu_ws/src/patrulha_tb4
python3 -m pytest -q                  # 134 testes, menos de 1 s
python3 test/checar_rastreio.py       # todo requisito L0 da spec patrol-inf tem teste?
cd ../lab_tb4 && python3 -m pytest -q # 17 testes: cenários do L1 e conferidor
```

Conferir uma configuração contra o mapa, antes de o robô andar (só dentro de um container, por causa do `pkg://`):

```bash
infra/docker/lab.sh sim compose run --rm -e COMPILAR_WS=patrulha_tb4 ferramentas \
  validar_pontos /workspace/meu_ws/src/patrulha_tb4/config/leve_reduzido.yaml
```

## 2. Imagens (só no PC do laboratório)

```bash
infra/docker/construir_imagem.sh base robo sim   # recusa com menos de 12 GiB de RAM (o notebook)
docker images 'physical-ai'                      # as Jazzy antigas ficam como physical-ai:jazzy-<alvo>
```

Construa `base` e `robo` juntas. Se só a `robo` for construída, a `base` continua Jazzy, e o `lab.sh robo` recusa (SEG-01).

## 3. Simulação no PC: Gazebo, o simulador principal (ADR-002)

Rede isolada e domínio 42: não alcança o robô real.

```bash
infra/docker/lab.sh sim subir gazebo slam rviz   # espere cerca de 1 min (./lab.sh sim logs gazebo)
infra/docker/lab.sh sim undock                   # tira o robô simulado da doca
infra/docker/lab.sh sim teleop                   # dirige pelo teclado, a 0,15 m/s
infra/docker/lab.sh sim salvar teste_maze        # grava em workspace/mapas/ e confere
infra/docker/lab.sh sim parar
```

`MUNDO=depot infra/docker/lab.sh sim subir gazebo` troca o mundo (`maze` é o padrão).

## 4. Simulador leve e os 11 cenários L1 (no PC)

Os cenários de falha (dock que falha, bateria que cai, servidor ausente) rodam no simulador leve: o `nav2_loopback_sim` vendorizado e a base falsa.

```bash
infra/docker/teste_l1.sh lista            # os 11 cenários
infra/docker/teste_l1.sh ciclo            # ciclo de recarga completo
infra/docker/teste_l1.sh dock_falha       # o dock falha 1 vez e a patrulha tenta de novo
```

Cada execução deixa uma pasta em `workspace/logs/l1/` com o log JSONL, os logs do Nav2, da base falsa e da patrulha, e o veredito (APROVADO ou REPROVADO). Os parâmetros de cada cenário estão em `workspace/meu_ws/src/lab_tb4/config/cenarios_l1.yaml`.

O leve à mão, sem cenário: `infra/docker/lab.sh sim subir leve` (não junto com o `gazebo`).

## 5. Robô real (no PC)

**ATENÇÃO (2026-11-16):** não use o `lab.sh robo` até a imagem Humble ser verificada com o robô (V5 de `specs/migracao-humble/DESIGN.md`). Nós Jazzy derrubaram o robô, que é Humble. As imagens agora são Humble, e o `lab.sh` recusa imagem de outra distro, mas o teste com o robô ainda não foi feito.

Mapa no robô real, só depois das etapas 1 a 3 do kit de campo (`specs/patrol-inf/kit-de-campo.md`):

```bash
infra/docker/lab.sh robo checar-rede      # só lê: rotas, e /robot1/scan, /robot1/tf e /robot1/odom chegam?
infra/docker/lab.sh robo subir slam rviz  # confere a rede e sobe (não move o robô)
infra/docker/lab.sh robo teleop           # move o robô REAL: pede que você digite SIM
infra/docker/lab.sh robo salvar lab
infra/docker/lab.sh robo parar
```

Patrulha no robô real (kit de campo, etapas 5 a 8):

```bash
MAPA=/mapas/lab.yaml infra/docker/lab.sh robo subir localizacao nav2 rviz
CONFIG=/mapas/inf_lab_preenchido.yaml infra/docker/lab.sh robo patrulha   # validar_pontos + SIM antes de andar
```

- O que está rodando: `infra/docker/lab.sh robo estado`.
- Conferir um mapa: `infra/docker/lab.sh conferir workspace/mapas/lab.yaml`.
- O robô do lab é Humble, usa Discovery Server e o namespace `/robot1` (`ROBO_NS` muda; `ROBO_NS=` para nenhum).
- O PC precisa de rotas pelo robô para `192.168.186.0/24` e `192.168.185.0/24`: o `checar-rede` mostra o comando.
- Acesso ao robô por cabo e por Wi-Fi: `docs/guias/acesso-ao-robo.md`. A rede do PC fica em `infra/lab/rede_lab.env`.

## Onde está a explicação

| Assunto | Arquivo |
|---|---|
| A migração para Humble (requisitos, design, fases) | `specs/migracao-humble/` e `docs/tarefas/2026-11-18-f*.md` |
| A patrulha (requisitos e testes) | `specs/patrol-inf/` |
| O que mudou e quando | `docs/tarefas/README.md` (e `docs/historico/registro-de-mudancas.md` até 2026-11-16) |

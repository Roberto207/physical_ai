# Correção do CI

**Data:** 2026-11-25

**Resposta direta:** o job `L0` falhava porque `workspace/meu_ws/src/patrulha_tb4/test/test_envio_base_assincrono.py` importa módulos do ROS, e o CI roda sem o ROS carregado. O erro de importação interrompia a suíte, e as etapas seguintes não rodavam. O arquivo agora é pulado onde não há ROS.

## Efeito

- No CI esse arquivo (2 testes) fica como pulado. Para rodá-lo, use uma imagem do projeto: `docker run --rm --network none -v "$PWD:/repo:ro" -w /repo/workspace/meu_ws/src/patrulha_tb4 physical-ai:base python3 -m pytest -q -p no:cacheprovider test/test_envio_base_assincrono.py`.
- As etapas de rastreio, `lab_tb4` e `llm_tb4` passam a rodar.

## Como foi verificado

As quatro etapas de teste, na ordem do workflow, em `ros:humble-ros-base` sem rede: `patrulha_tb4` 155 aprovados e 1 pulado, rastreio dos 35 requisitos, `lab_tb4` 17, `llm_tb4` 233. Na `physical-ai:base`, os 2 testes do arquivo passam.

**Não verificado até o envio:** a execução no GitHub.

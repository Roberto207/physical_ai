# Pontos no `mapa_lab_novo`

Medidos no referencial `map`, em metros. Os graus (`yaw`) anotados **não são usados** pelos programas de `workspace/patrulha_oficial/`, que calculam a orientação pela direção do ponto seguinte. Os valores usados no código ficam em `workspace/patrulha_oficial/patrol_loop.py` (`PONTOS`): ao mudar um, mude nos dois.

Os nomes pelos quais a LLM reconhece cada ponto estão em `workspace/meu_ws/src/llm_tb4/config/destinos.json` (25/11).

```text
ponto inicial
x: -0.2025940716266632
y: 0.10048891603946686
yaw_graus: 38.478622669484366

ponto 1 - pouco à frente do início
x: -0.5858250856399536
y: -0.8073815107345581
yaw_graus: 38.478622669484366

ponto 2 - perto da geladeirinha
x: -3.549771785736084
y: -3.0633668899536133
yaw_graus: 90

ponto 3 - direita em cima, no mapa
x: -5.608144283294678
y: -0.8229406476020813
yaw_grau: 10

ponto 4 - meio direita, no mapa
x: -1.9671252965927124
y: 1.0304899215698242
yaw_graus: 51.28233242603174
```

# Mapas feitos por nós (SLAM)

Esta pasta fica no git de propósito: é por ela que o mapa feito no PC do laboratório chega ao notebook (a pasta `workspace/logs/` está no `.gitignore`).

Cada mapa tem três arquivos, gravados por `infra/docker/lab.sh <modo> salvar <nome>`:

| Arquivo | O que é |
|---|---|
| `<nome>.yaml` | Metadados do `map_saver`: imagem, resolução, origem e limiares |
| `<nome>.pgm` | A imagem do mapa: branco é livre, preto é parede, cinza é não mapeado |
| `<nome>.info.txt` | Nossa ficha: data, modo (`sim` ou `robo`), se começou na doca e a versão do código |

## O que há aqui

| Arquivo | O que é |
|---|---|
| `mapa_lab_novo.yaml` e `.pgm` | **O mapa em uso no robô** (sem `.info.txt`). É o padrão do serviço `localizacao` |
| `pontos_mapa_lab_novo.md` | Coordenadas da doca e dos quatro pontos usados pela patrulha |
| `patrulha_mapa_lab_novo.yaml` | Não é um mapa: é a configuração da `patrulha_tb4` (programa anterior) para esse mapa |

Os programas de `workspace/patrulha_oficial/` têm os pontos no próprio código e não leem arquivo de configuração. Se o mapa mudar, os pontos precisam ser medidos de novo.

Para uma configuração nova da `patrulha_tb4`, copie `workspace/meu_ws/src/patrulha_tb4/config/inf_lab.yaml` para esta pasta e siga a seção 6 de `docs/guias/como-rodar.md`.

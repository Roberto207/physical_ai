# Mapas feitos por nós (SLAM)

Esta pasta fica no git de propósito: é por ela que o mapa feito no PC do laboratório chega ao notebook (a pasta `progresso/` está no `.gitignore`).

Cada mapa tem três arquivos, gravados por `infra/docker/lab.sh <modo> salvar <nome>`:

| Arquivo | O que é |
|---|---|
| `<nome>.yaml` | Metadados do `map_saver`: imagem, resolução, origem e limiares |
| `<nome>.pgm` | A imagem do mapa: branco é livre, preto é parede, cinza é não mapeado |
| `<nome>.info.txt` | Nossa ficha: data, modo (`sim` ou `robo`), se começou na doca e a versão do código |

Para usar na patrulha, copie o `config/inf_lab.yaml` para esta pasta (por exemplo, `inf_lab_preenchido.yaml`), preencha e deixe `mapa: lab.yaml`. O caminho é relativo ao arquivo, então funciona dentro do container (`/mapas/`) e fora dele. Depois rode o `validar_pontos`. Passo a passo em `docs/tarefas/2026-11-16-compose-e-alvos.md`.

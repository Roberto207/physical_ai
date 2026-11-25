# Specs: o que o sistema precisa fazer

| Pasta | Assunto | Estado |
|---|---|---|
| `specs/preflight-robo/` | Checagens antes de a patrulha mover o robô (skill `preflight-robo`) | Aprovada e implementada em 25/11; falta validar com o robô |
| `specs/llm-integracao/` | Integração com LLM (Ollama) | Execução escrita e ensaiada com robô falso; falta simulador e robô |
| `specs/patrol-inf/` | Patrulha com recarga (`patrulha_tb4`) | Aprovada em 10/11. O DESIGN é lido por um teste (`test/checar_rastreio.py`). O `kit-de-campo.md` é anterior ao uso atual do robô |
| `specs/migracao-humble/` | Migração das imagens para ROS 2 Humble | Aprovada em 18/11. Código feito; os IDs (SEG, IMG, SIM) são citados no código. Parte das verificações não tem registro |

A spec do enxugamento (18/11), já executada, está em `docs/historico/spec-enxugamento.md`. Para operar o robô hoje, use `docs/guias/como-rodar.md`.

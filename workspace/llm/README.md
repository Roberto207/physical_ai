# Integração com LLM

Missão 2 do projeto (`docs/contexto/projeto.md`): comandar o TurtleBot 4 por linguagem natural.

## Modelo

**Ollama** com `qwen2.5:1.5b` (decidido em 25/11), gratuito e executado localmente. A [página do modelo](https://ollama.com/library/qwen2.5) informa 986 MB e contexto de 32K, e lista suporte a *tools* para a família.

Instalado no PC do laboratório em 25/11 (Ollama 0.40.18, como serviço, em `127.0.0.1:11434`).

```bash
ollama list                      # o modelo está baixado?
ollama pull qwen2.5:1.5b         # baixar (cerca de 986 MB)
systemctl status ollama          # o serviço está ativo?
```

## Arquivos

| Arquivo | O que faz |
|---|---|
| `interpretador.py` | Frase → ação validada. Decide "parar" sem o modelo; recusa negação e dois destinos; consulta o Ollama; valida |
| `validar_acao.py` | Aceita só `ir_para` (local conhecido, bateria a partir de 20%), `voltar_para_base` e `parar` |
| `destinos.json` | Locais que podem ser pedidos e a que ponto da patrulha correspondem |
| `prompts/comandos.txt` | Instruções e exemplos enviados ao modelo |
| `avaliar.py` e `testes_frases/` | Medição com o modelo real |
| `test_interpretador.py`, `test_validar_acao.py` | Testes sem Ollama e sem ROS |

## Usar (nada aqui move o robô)

```bash
cd ~/physical_ai/workspace/llm
python3 interpretador.py "vá até a geladeirinha"     # mostra a decisão
python3 avaliar.py                                   # acertos, erros e tempo com o modelo real
# testes sem modelo, na imagem do projeto (o python3 do PC não tem pytest)
docker run --rm --network none -v "$PWD:/llm:ro" -w /llm physical-ai:base python3 -m pytest -q -p no:cacheprovider
```

**Ainda não existe:** nó ROS e execução no robô. Plano e medições: `specs/llm-integracao/PLANO.md`.

## Regra de desenho

A LLM só escolhe entre ações discretas validadas; nada do que ela escreve é executado como código (sem `exec`). O registro está em `docs/decisoes/README.md` como proposta a confirmar com a equipe. O modelo erra: nenhum movimento sem confirmação humana. O tutorial oficial `turtlebot4_openai_tutorials` serve de referência, não de base.

## De onde reaproveitar

- Exemplos oficiais: ver "Referências oficiais" em `docs/contexto/stack.md`.
- Locais: `workspace/mapas/pontos_mapa_lab_novo.md`.
- Navegar, esperar a localização, encaixar na doca: funções de `workspace/patrulha_oficial/patrol_loop.py`.

Decisões em aberto: `docs/contexto/pendencias.md`.

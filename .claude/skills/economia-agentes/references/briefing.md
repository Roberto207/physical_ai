# Briefing de subagente

Todo prompt de subagente tem estes campos, nesta ordem:

    OBJETIVO: 1 frase
    ENTRADAS: só caminhos de arquivo (proibido colar mais de 20 linhas de texto)
    NÃO FAÇA: executar comando que alcance o robô físico; editar o repositório (se for avaliação);
              chamar outros agentes; <específico da tarefa>
    SAÍDA: grava o resultado em <caminho>
    RETORNO: status | caminho | até 10 linhas de achados | lacunas (máx. ~1.500 tokens; o detalhe fica no arquivo)
    PRONTO QUANDO: <critério verificável>
    TETO: até N chamadas de ferramenta (3–10 em tarefa simples, 10–15 em comparação)

Exemplo (leitura de log):

    OBJETIVO: achar a primeira falha do Nav2 no log da patrulha.
    ENTRADAS: /tmp/<arquivo>.log (saída de docker logs tb_nav2)
    NÃO FAÇA: executar comando que alcance o robô físico; chamar outros agentes; editar código; subir simulação.
    SAÍDA: grava o resultado em /tmp/diagnostico_nav2.md
    RETORNO: status | caminho | até 10 linhas: horário, nó, mensagem de erro e o que veio antes
    PRONTO QUANDO: a primeira linha de erro está citada com o número da linha no log.
    TETO: até 8 chamadas de ferramenta.

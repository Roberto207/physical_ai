#!/usr/bin/env python3
"""Confere o log JSONL de uma execução da patrulha contra o esperado de um cenário.

Python puro, sem ROS. Roda dentro do container (para saber a hora de parar o teste) e
no notebook (para dar o veredito da evidência).

    python3 conferir_l1.py <cenario> <arquivo.jsonl>            veredito completo
    python3 conferir_l1.py <cenario> <arquivo.jsonl> --pronto   só diz se já dá para parar
    python3 conferir_l1.py <cenario> <arquivo.jsonl> --sinal T  confere também o prazo do
                                                                Ctrl+C enviado no instante T

Sai com 0 se passou (ou se está pronto), 1 se não.
"""
import json
import sys

PRAZO_CICLO_S = 15 * 60   # TST-03, tempo de relógio
PRAZO_REACAO_S = 2.0      # PAT-06
PRAZO_ENCERRAR_S = 3.0    # PAT-15


def ler(caminho):
    eventos = []
    try:
        with open(caminho, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if linha:
                    eventos.append(json.loads(linha))
    except FileNotFoundError:
        pass
    return eventos


def nomes(eventos):
    return [e['evento'] for e in eventos]


def indice(eventos, nome, a_partir=0, **campos):
    """Posição do primeiro evento com esse nome (e esses campos) a partir de `a_partir`, ou None."""
    for i in range(a_partir, len(eventos)):
        e = eventos[i]
        if e['evento'] == nome and all(e.get(c) == v for c, v in campos.items()):
            return i
    return None


def codigo_de_saida(eventos):
    for e in reversed(eventos):
        if e['evento'] == 'resumo':
            return e.get('codigo_saida')
    return None


def fim_do_ciclo(eventos):
    """Posição do destino_ok que fecha o ciclo de recarga (definição do DEFINE), ou None.

    Sair da doca, pelo menos 2 pontos, ida à doca por bateria baixa, dock confirmado,
    carga até `alta`, undock e mais 1 ponto com sucesso.
    """
    saida = indice(eventos, 'undock_ok')
    if saida is None:
        return None
    baixa = indice(eventos, 'bateria_baixa', saida)
    if baixa is None:
        return None
    if nomes(eventos[saida:baixa]).count('destino_ok') < 2:
        return None
    passo = baixa
    for nome in ('dock_ok', 'carga_completa', 'undock_ok', 'destino_ok'):
        passo = indice(eventos, nome, passo + 1)
        if passo is None:
            return None
    return passo


def base(eventos, problemas):
    """O que vale para toda execução: início primeiro (OBS-03) e campos obrigatórios (OBS-01)."""
    if not eventos:
        problemas.append('log vazio ou inexistente')
        return
    if eventos[0]['evento'] != 'inicio':
        problemas.append('o primeiro evento não é "inicio"')
    for campo in ('hash_codigo', 'hash_config', 'versao', 'ambiente', 'modelo'):
        if campo not in eventos[0]:
            problemas.append(f'inicio sem o campo {campo}')
    for i, e in enumerate(eventos):
        faltam = [c for c in ('t', 't_parede', 'evento', 'estado', 'bateria') if c not in e]
        if faltam:
            problemas.append(f'linha {i + 1} sem {faltam}')


def exigir_saida(eventos, problemas, codigo, evento):
    """OBS-02: o resumo fecha o log com o código esperado, logo depois do evento de saída."""
    if codigo_de_saida(eventos) != codigo:
        problemas.append(f'código de saída {codigo_de_saida(eventos)}, esperado {codigo}')
    if eventos and eventos[-1]['evento'] != 'resumo':
        problemas.append('o último evento não é "resumo"')
    if evento not in nomes(eventos):
        problemas.append(f'faltou o evento {evento}')


def sem_acao(eventos, problemas):
    for proibido in ('undock_ok', 'undock_falhou', 'destino_enviado', 'dock_ok'):
        if proibido in nomes(eventos):
            problemas.append(f'houve {proibido}, mas nenhuma ação deveria ter sido enviada')


def ciclo(eventos, problemas):
    fim = fim_do_ciclo(eventos)
    if fim is None:
        problemas.append('o ciclo de recarga não fechou: ' + ' > '.join(nomes(eventos)[-8:]))
        return
    duracao = eventos[fim]['t_parede'] - eventos[0]['t_parede']
    print(f'  ciclo de recarga fechado em {duracao:.0f} s de relógio (limite: {PRAZO_CICLO_S} s)')
    if duracao > PRAZO_CICLO_S:
        problemas.append(f'ciclo em {duracao:.0f} s, acima do limite do TST-03')
    cancelado = indice(eventos, 'destino_cancelado')
    carga = indice(eventos, 'carga_completa', cancelado or 0)
    if cancelado is not None and carga is not None:
        retomado = indice(eventos, 'destino_enviado', carga, ponto=eventos[cancelado]['ponto'])
        if retomado is None:
            problemas.append('depois da recarga, não reenviou o ponto interrompido (PAT-13)')


def dock_falha(eventos, problemas):
    falha = indice(eventos, 'dock_nao_confirmado')
    if falha is None:
        problemas.append('não houve dock_nao_confirmado: a falha não foi provocada')
        return
    if indice(eventos, 'dock_ok', falha) is None:
        problemas.append('não houve dock_ok depois da falha (TST-04)')
    if nomes(eventos).count('dock_nao_confirmado') != 1:
        problemas.append('esperava exatamente 1 dock_nao_confirmado')


def queda_bateria(eventos, problemas):
    baixa = indice(eventos, 'bateria_baixa')
    if baixa is None:
        problemas.append('não houve bateria_baixa')
        return
    cancelado = indice(eventos, 'destino_cancelado', baixa)
    enviado = indice(eventos, 'destino_enviado', baixa)
    if cancelado is None:
        problemas.append('a bateria baixou sem destino em andamento: não prova o PAT-06')
        return
    if enviado is None or not str(eventos[enviado].get('detalhe', '')).startswith('aproximacao'):
        problemas.append('não enviou a aproximação da doca depois do cancelamento')
        return
    idade = 0.0
    detalhe = str(eventos[baixa].get('detalhe', ''))
    if detalhe.startswith('idade_bateria_s='):
        idade = float(detalhe.split('=')[1])
    reacao = idade + eventos[enviado]['t_parede'] - eventos[baixa]['t_parede']
    print(f'  da bateria recebida ao destino da doca enviado: {reacao:.2f} s '
          f'(limite: {PRAZO_REACAO_S} s)')
    if reacao > PRAZO_REACAO_S:
        problemas.append(f'reação em {reacao:.2f} s, acima do limite do PAT-06')


def sem_bateria(eventos, problemas):
    exigir_saida(eventos, problemas, 3, 'sem_bateria')
    sem_acao(eventos, problemas)


def fora_da_doca(eventos, problemas):
    exigir_saida(eventos, problemas, 6, 'fora_da_doca')
    sem_acao(eventos, problemas)


def sem_servidor(eventos, problemas):
    exigir_saida(eventos, problemas, 8, 'servidor_indisponivel')
    sem_acao(eventos, problemas)


def sem_relogio(eventos, problemas):
    exigir_saida(eventos, problemas, 9, 'sem_relogio')
    sem_acao(eventos, problemas)


def bateria_perdida(eventos, problemas):
    exigir_saida(eventos, problemas, 3, 'bateria_perdida')
    primeira = indice(eventos, 'bateria_perdida')
    if primeira is None:
        return
    if eventos[primeira].get('detalhe') == 'na_doca':
        problemas.append('a perda só apareceu na doca: faltou a perda fora da doca (PAT-18)')
    if indice(eventos, 'dock_ok', primeira) is None:
        problemas.append('não voltou à doca depois de perder a bateria (PAT-18)')
    if indice(eventos, 'bateria_perdida', primeira + 1, detalhe='na_doca') is None:
        problemas.append('não encerrou pela perda já na doca (PAT-18b)')
    depois = eventos[primeira:]
    if any(e['evento'] == 'destino_enviado' and 'ponto' in e for e in depois):
        problemas.append('visitou ponto de patrulha depois de perder a bateria')


def falhas_seguidas(eventos, problemas):
    exigir_saida(eventos, problemas, 7, 'falhas_seguidas')
    if nomes(eventos).count('destino_falhou') < 3:
        problemas.append('menos de 3 destino_falhou')
    dock = indice(eventos, 'dock_ok')
    fim = indice(eventos, 'falhas_seguidas')
    if dock is None or fim is None or fim < dock:
        problemas.append('não encerrou depois do dock confirmado (PAT-08)')


def sigint(eventos, problemas):
    exigir_saida(eventos, problemas, 0, 'encerrado')
    if 'destino_enviado' not in nomes(eventos):
        problemas.append('o sinal chegou antes de qualquer destino: não prova o cancelamento')


def encerramento(eventos, problemas, t_sinal):
    """PAT-15: do SIGINT ao resumo gravado, em até 3 s de relógio, com o código 0."""
    resumo = indice(eventos, 'resumo')
    if resumo is None or indice(eventos, 'encerrado') is None:
        problemas.append('recebeu SIGINT e não gravou "encerrado" e "resumo" (PAT-15)')
        return
    demora = eventos[resumo]['t_parede'] - t_sinal
    print(f'  do SIGINT ao resumo gravado: {demora:.2f} s (limite: {PRAZO_ENCERRAR_S} s)')
    if demora > PRAZO_ENCERRAR_S:
        problemas.append(f'encerrou em {demora:.2f} s, acima do limite do PAT-15')
    if eventos[resumo].get('codigo_saida') != 0:
        problemas.append('o código de saída depois do SIGINT não foi 0')


CENARIOS = {
    # nome: (função de veredito, função "já dá para parar")
    'ciclo': (ciclo, lambda ev: fim_do_ciclo(ev) is not None),
    'l1b': (ciclo, lambda ev: fim_do_ciclo(ev) is not None),
    'dock_falha': (dock_falha, lambda ev: 'dock_ok' in nomes(ev)),
    'queda_bateria': (queda_bateria, lambda ev: 'dock_ok' in nomes(ev)),
    'sem_bateria': (sem_bateria, lambda ev: False),
    'fora_da_doca': (fora_da_doca, lambda ev: False),
    'sem_servidor': (sem_servidor, lambda ev: False),
    'sem_relogio': (sem_relogio, lambda ev: False),
    'bateria_perdida': (bateria_perdida, lambda ev: False),
    'falhas_seguidas': (falhas_seguidas, lambda ev: False),
    'sigint': (sigint, lambda ev: nomes(ev).count('destino_ok') >= 1),
}


def main(argumentos):
    if len(argumentos) < 2 or argumentos[0] not in CENARIOS:
        print(__doc__)
        print('Cenários: ' + ', '.join(CENARIOS))
        return 2
    cenario, caminho = argumentos[0], argumentos[1]
    eventos = ler(caminho)
    veredito, pronto = CENARIOS[cenario]
    if '--pronto' in argumentos:
        return 0 if (pronto(eventos) or codigo_de_saida(eventos) is not None) else 1

    problemas = []
    base(eventos, problemas)
    if eventos:
        veredito(eventos, problemas)
        if '--sinal' in argumentos:
            encerramento(eventos, problemas, float(argumentos[argumentos.index('--sinal') + 1]))
        print(f'  {len(eventos)} eventos; código de saída no resumo: {codigo_de_saida(eventos)}')
        print(f'  hash_codigo: {eventos[0].get("hash_codigo", "?")[:16]}...')
    if problemas:
        print(f'REPROVADO ({cenario}):')
        for problema in problemas:
            print(f'  - {problema}')
        return 1
    print(f'APROVADO ({cenario})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

"""Testes da máquina de estados da patrulha (L0). Cada teste diz qual requisito prova."""
import math

import pytest
from conftest import Mundo, fazer_config

from patrulha_tb4 import decisao as d


def entrada(**campos):
    padrao = dict(parede=1110.0, agora=110.0, bateria=0.5, t_bateria=110.0, na_base=False,
                  servidores_ok=True)
    padrao.update(campos)
    return d.Entrada(**padrao)


def estado(cfg, fase, **campos):
    padrao = dict(fase=fase, parede_inicio=1000.0, t_inicio=0.0, limites=cfg.limites)
    padrao.update(campos)
    return d.Estado(**padrao)


def patrulhando(cfg, **campos):
    padrao = dict(acao=d.DESTINO, t_acao=100.0, indice=1)
    padrao.update(campos)
    return estado(cfg, d.PATRULHANDO, **padrao)


def nomes(saida):
    return [evento['evento'] for evento in saida.eventos]


def acoes(saida):
    return [acao[0] for acao in saida.acoes]


# ---------------------------------------------------------------- início

@pytest.mark.req('PAT-03')
def test_espera_a_primeira_bateria_sem_enviar_acao(cfg):
    saida = d.decidir(estado(cfg, d.INICIANDO), entrada(agora=29.0, bateria=None, t_bateria=None,
                                                         na_base=True), cfg)
    assert saida.acoes == () and saida.estado.fase == d.INICIANDO


@pytest.mark.req('PAT-03')
@pytest.mark.req('PAT-04')
def test_sem_bateria_encerra_com_codigo_3_sem_nenhuma_acao(cfg):
    mundo = Mundo(cfg, publica_bateria=False).rodar(60)
    assert mundo.codigo == d.CODIGO_SEM_BATERIA
    assert mundo.nomes() == ['sem_bateria']
    assert mundo.acoes_enviadas() == [d.ENCERRAR]
    assert mundo.t == 32.0  # passa de 30 s contados da primeira chamada, que foi em t=1


@pytest.mark.req('PAT-20')
def test_servidor_indisponivel_encerra_com_codigo_8(cfg):
    mundo = Mundo(cfg, servidores_ok=False).rodar(60)
    assert mundo.codigo == d.CODIGO_SERVIDOR
    assert mundo.nomes() == ['servidor_indisponivel']
    assert mundo.acoes_enviadas() == [d.ENCERRAR]


@pytest.mark.req('PAT-17')
def test_comecar_fora_da_doca_encerra_com_codigo_6(cfg):
    mundo = Mundo(cfg, na_base=False, bateria=0.99).rodar(10)
    assert mundo.codigo == d.CODIGO_FORA_DA_DOCA
    assert mundo.nomes() == ['fora_da_doca']
    assert d.UNDOCK not in mundo.acoes_enviadas() and d.DESTINO not in mundo.acoes_enviadas()


def test_sem_dock_status_no_inicio_nao_fica_parado_para_sempre(cfg):
    mundo = Mundo(cfg, publica_doca=False, bateria=0.99, carga=0.0).rodar(60)
    assert mundo.codigo == d.CODIGO_SERVIDOR
    assert mundo.eventos[-1]['detalhe'] == 'dock_status'


@pytest.mark.req('PAT-12')
def test_na_doca_abaixo_de_alta_nao_sai_ate_carregar(cfg):
    mundo = Mundo(cfg, bateria=0.5, carga=0.05)
    mundo.rodar(8)  # 0,5 + 8 x 0,05 = 0,90: ainda abaixo de 0,95
    assert mundo.acoes == [] and mundo.estado.fase == d.CARREGANDO
    mundo.rodar(2)
    assert mundo.acoes_enviadas() == [d.UNDOCK]


# ---------------------------------------------------------------- patrulha e bateria

@pytest.mark.req('PAT-05')
def test_bateria_e_conferida_a_cada_chamada_durante_o_destino(cfg):
    assert d.PERIODO_S <= 1.0
    saida = d.decidir(patrulhando(cfg), entrada(bateria=0.5), cfg)
    assert saida.acoes == () and saida.eventos == ()
    saida = d.decidir(saida.estado, entrada(agora=111.0, t_bateria=111.0, bateria=0.19), cfg)
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]


@pytest.mark.req('PAT-06')
def test_bateria_baixa_no_meio_do_trecho_cancela_e_vai_a_doca(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(bateria=0.19), cfg)
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]  # na mesma chamada: sem esperar
    assert nomes(saida) == ['bateria_baixa', 'destino_cancelado', 'destino_enviado']
    assert saida.eventos[1]['ponto'] == 1
    assert saida.estado.fase == d.INDO_DOCA
    assert saida.estado.indice == 1  # o ponto interrompido continua sendo o atual


@pytest.mark.req('PAT-06')
def test_bateria_igual_a_baixa_nao_dispara(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(bateria=cfg.limites.baixa), cfg)
    assert saida.acoes == ()


@pytest.mark.req('PAT-14')
def test_bateria_critica_cancela_e_vai_a_doca_e_prevalece_sobre_a_baixa(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(bateria=0.09), cfg)
    assert nomes(saida) == ['bateria_critica', 'destino_cancelado', 'destino_enviado']
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]
    assert d.DESTINO not in acoes(saida)


@pytest.mark.req('PAT-14')
def test_bateria_critica_nao_reage_de_novo_quando_ja_esta_indo_a_doca(cfg):
    indo = estado(cfg, d.INDO_DOCA, acao=d.APROXIMACAO, t_acao=100.0, motivo_doca=d.POR_BATERIA)
    saida = d.decidir(indo, entrada(bateria=0.05), cfg)
    assert saida.acoes == () and saida.eventos == ()


@pytest.mark.req('PAT-14')
def test_bateria_critica_durante_o_undock_fora_da_doca(cfg):
    saindo = estado(cfg, d.SAINDO_DOCA, acao=d.UNDOCK, t_acao=100.0)
    saida = d.decidir(saindo, entrada(bateria=0.05, na_base=False), cfg)
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]
    assert nomes(saida)[0] == 'bateria_critica'


@pytest.mark.req('PAT-07')
def test_destino_falho_grava_o_ponto_e_o_codigo(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(resultado=d.Resultado(d.DESTINO, d.FALHOU, 6)), cfg)
    assert saida.eventos[0] == {'evento': 'destino_falhou', 'ponto': 1, 'resultado': 6}


@pytest.mark.req('PAT-07b')
def test_depois_de_um_destino_falho_envia_o_proximo_ponto(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(resultado=d.Resultado(d.DESTINO, d.FALHOU, 6)), cfg)
    assert saida.acoes == ((d.DESTINO, 2),)
    assert saida.estado.falhas_seguidas == 1


@pytest.mark.req('PAT-08')
def test_terceiro_destino_falho_seguido_vai_a_doca_e_encerra_com_7_depois_do_dock(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0001, pontos_inalcancaveis={0, 1, 2}).rodar(200)
    assert mundo.codigo == d.CODIGO_FALHAS
    eventos = mundo.nomes()
    assert eventos.count('destino_falhou') == 3
    assert eventos[-2:] == ['dock_ok', 'falhas_seguidas']  # só encerra com o dock confirmado
    assert eventos.index('dock_ok') > eventos.index('destino_falhou')


@pytest.mark.req('PAT-08')
def test_contador_de_falhas_zera_com_um_sucesso(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0001, pontos_inalcancaveis={0, 1}).rodar(150)
    assert mundo.codigo is None  # falha, falha, sucesso, falha, falha, sucesso...
    assert mundo.nomes().count('destino_falhou') >= 4
    assert 'falhas_seguidas' not in mundo.nomes()


@pytest.mark.req('PAT-08')
def test_contador_de_falhas_zera_na_recarga_completa(cfg):
    carregando = estado(cfg, d.CARREGANDO, falhas_seguidas=2, motivo_doca=d.POR_BATERIA)
    saida = d.decidir(carregando, entrada(bateria=0.96, na_base=True), cfg)
    assert saida.estado.falhas_seguidas == 0


@pytest.mark.req('PAT-19')
def test_destino_que_passa_do_tempo_e_cancelado_e_conta_como_falho(cfg):
    antes = d.decidir(patrulhando(cfg), entrada(agora=220.0, t_bateria=220.0), cfg)
    assert antes.acoes == ()  # 120 s exatos ainda não estouram
    saida = d.decidir(patrulhando(cfg), entrada(agora=220.5, t_bateria=220.5), cfg)
    assert saida.eventos[0] == {'evento': 'destino_falhou', 'ponto': 1,
                                'resultado': 'tempo_esgotado'}
    assert saida.acoes == ((d.CANCELAR,), (d.DESTINO, 2))
    assert saida.estado.falhas_seguidas == 1


def test_volta_e_contada_ao_fechar_a_lista(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0).rodar(80)
    assert mundo.estado.voltas == 2
    pontos = [e['ponto'] for e in mundo.eventos if e['evento'] == 'destino_ok']
    assert pontos[:6] == [0, 1, 2, 0, 1, 2]


# ---------------------------------------------------------------- dock

@pytest.mark.req('PAT-09')
def test_dock_ok_exige_sucesso_da_acao_e_is_docked(cfg):
    encaixando = estado(cfg, d.ENCAIXANDO, acao=d.DOCK, t_acao=100.0, tentativas_dock=1,
                        motivo_doca=d.POR_BATERIA)
    # A ação deu sucesso, mas o /dock_status ainda diz "fora": espera, sem gravar nada.
    espera = d.decidir(encaixando, entrada(resultado=d.Resultado(d.DOCK, d.SUCESSO, 4)), cfg)
    assert espera.eventos == () and espera.estado.fase == d.ENCAIXANDO
    # O is_docked chega dentro dos 5 s.
    ok = d.decidir(espera.estado, entrada(agora=114.0, t_bateria=114.0, na_base=True), cfg)
    assert nomes(ok) == ['dock_ok'] and ok.estado.fase == d.CARREGANDO


@pytest.mark.req('PAT-09')
def test_dock_sem_is_docked_no_prazo_grava_dock_nao_confirmado(cfg):
    encaixando = estado(cfg, d.ENCAIXANDO, acao=d.DOCK, t_acao=100.0, tentativas_dock=1,
                        motivo_doca=d.POR_BATERIA)
    espera = d.decidir(encaixando, entrada(resultado=d.Resultado(d.DOCK, d.SUCESSO, 4)), cfg)
    saida = d.decidir(espera.estado, entrada(agora=115.5, t_bateria=115.5), cfg)
    assert nomes(saida)[0] == 'dock_nao_confirmado'
    assert 'dock_ok' not in nomes(saida)


@pytest.mark.req('PAT-09')
def test_acao_de_dock_que_falha_nunca_grava_dock_ok_mesmo_com_is_docked(cfg):
    encaixando = estado(cfg, d.ENCAIXANDO, acao=d.DOCK, t_acao=100.0, tentativas_dock=1,
                        motivo_doca=d.POR_BATERIA)
    saida = d.decidir(encaixando, entrada(na_base=True,
                                          resultado=d.Resultado(d.DOCK, d.FALHOU, 6)), cfg)
    assert nomes(saida)[0] == 'dock_nao_confirmado'
    assert 'dock_ok' not in nomes(saida)


@pytest.mark.req('PAT-10')
def test_dock_nao_confirmado_reaproxima_e_tenta_de_novo(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.02, falhar_dock=1).rodar(
        200, ate=lambda m: 'dock_ok' in m.nomes())
    eventos = mundo.nomes()
    assert eventos.count('dock_nao_confirmado') == 1 and eventos.count('dock_ok') == 1
    assert eventos.index('dock_nao_confirmado') < eventos.index('dock_ok')  # ok na 2ª tentativa
    assert mundo.acoes_enviadas().count(d.APROXIMACAO) == 2
    assert mundo.acoes_enviadas().count(d.DOCK) == 2


@pytest.mark.req('PAT-10')
@pytest.mark.req('PAT-11')
def test_tres_tentativas_de_dock_e_encerra_com_codigo_4(cfg):
    mundo = Mundo(cfg, bateria=0.25, descarga=0.01, dock_sem_confirmar=99).rodar(300)
    assert mundo.codigo == d.CODIGO_DOCK
    assert mundo.nomes().count('dock_nao_confirmado') == 3
    assert mundo.acoes_enviadas().count(d.DOCK) == 3
    assert mundo.nomes()[-1] == 'dock_falhou'
    assert mundo.acoes_enviadas()[-1] == d.ENCERRAR  # nenhuma ação nova depois de desistir


def test_aproximacao_que_falha_conta_como_tentativa_e_termina(cfg):
    indo = estado(cfg, d.INDO_DOCA, acao=d.APROXIMACAO, t_acao=100.0, tentativas_dock=2,
                  motivo_doca=d.POR_BATERIA)
    saida = d.decidir(indo, entrada(resultado=d.Resultado(d.APROXIMACAO, d.FALHOU, 6)), cfg)
    assert nomes(saida) == ['dock_nao_confirmado', 'dock_falhou']
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_DOCK),)


# ---------------------------------------------------------------- recarga

@pytest.mark.req('PAT-12')
def test_carregando_abaixo_de_alta_nao_envia_nada(cfg):
    carregando = estado(cfg, d.CARREGANDO, motivo_doca=d.POR_BATERIA)
    saida = d.decidir(carregando, entrada(bateria=0.94, na_base=True), cfg)
    assert saida.acoes == () and saida.eventos == ()


@pytest.mark.req('PAT-13')
def test_ciclo_de_recarga_retoma_o_mesmo_ponto(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.005, carga=0.05, duracao_destino=30)

    def ciclo_fechado(m):
        nomes_ = m.nomes()
        return 'carga_completa' in nomes_ and \
            'destino_ok' in nomes_[nomes_.index('carga_completa'):]

    mundo.rodar(600, ate=ciclo_fechado)
    eventos = mundo.eventos
    nomes_ = mundo.nomes()
    assert mundo.codigo is None
    for esperado in ('undock_ok', 'bateria_baixa', 'destino_cancelado', 'dock_ok',
                     'carga_completa'):
        assert esperado in nomes_
    interrompido = next(e['ponto'] for e in eventos if e['evento'] == 'destino_cancelado')
    depois_da_carga = eventos[nomes_.index('carga_completa'):]
    retomado = next(e['ponto'] for e in depois_da_carga if e['evento'] == 'destino_enviado')
    assert retomado == interrompido
    assert nomes_.count('undock_ok') == 2
    assert mundo.bateria_minima >= cfg.limites.critica  # nunca chegou perto de zerar


# ---------------------------------------------------------------- encerramentos

@pytest.mark.req('PAT-15')
def test_sinal_cancela_a_acao_ativa_e_encerra_com_0(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(sinal=True), cfg)
    assert saida.acoes == ((d.CANCELAR,), (d.ENCERRAR, d.CODIGO_ENCERRADO))
    assert nomes(saida) == ['encerrado']
    assert saida.estado.fase == d.ENCERRANDO and saida.estado.codigo_saida == 0


@pytest.mark.req('PAT-15')
def test_sinal_sem_acao_ativa_so_encerra(cfg):
    carregando = estado(cfg, d.CARREGANDO)
    saida = d.decidir(carregando, entrada(sinal=True, na_base=True), cfg)
    assert saida.acoes == ((d.ENCERRAR, 0),)


def test_depois_de_encerrar_nao_decide_mais_nada(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(sinal=True), cfg)
    de_novo = d.decidir(saida.estado, entrada(bateria=0.01), cfg)
    assert de_novo.acoes == () and de_novo.eventos == ()


@pytest.mark.req('PAT-16')
def test_undock_que_falha_encerra_com_5_sem_patrulhar(cfg):
    mundo = Mundo(cfg, bateria=0.99, falhar_undock=True).rodar(30)
    assert mundo.codigo == d.CODIGO_UNDOCK
    assert mundo.nomes() == ['undock_falhou']
    assert d.DESTINO not in mundo.acoes_enviadas()


# ---------------------------------------------------------------- bateria perdida

@pytest.mark.req('PAT-18')
def test_bateria_perdida_no_trecho_cancela_e_vai_a_doca_uma_vez(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(agora=121.0, t_bateria=110.0), cfg)
    assert nomes(saida) == ['bateria_perdida', 'destino_cancelado', 'destino_enviado']
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]
    # Já indo à doca: segue, e não grava o evento de novo.
    de_novo = d.decidir(saida.estado, entrada(agora=125.0, t_bateria=110.0), cfg)
    assert de_novo.acoes == () and de_novo.eventos == ()


@pytest.mark.req('PAT-18')
def test_bateria_perdida_respeita_o_tempo_da_configuracao():
    cfg = fazer_config(ambiente='gazebo')  # 30 s no gazebo
    saida = d.decidir(patrulhando(cfg), entrada(agora=139.0, t_bateria=110.0), cfg)
    assert saida.acoes == ()
    saida = d.decidir(patrulhando(cfg), entrada(agora=141.0, t_bateria=110.0), cfg)
    assert nomes(saida)[0] == 'bateria_perdida'


@pytest.mark.req('PAT-18')
def test_bateria_perdida_volta_a_ser_gravada_depois_de_uma_mensagem_nova(cfg):
    indo = estado(cfg, d.INDO_DOCA, acao=d.APROXIMACAO, t_acao=100.0, perda_gravada=True,
                  motivo_doca=d.POR_BATERIA)
    voltou = d.decidir(indo, entrada(agora=130.0, t_bateria=130.0), cfg)
    assert voltou.estado.perda_gravada is False
    sumiu = d.decidir(voltou.estado, entrada(agora=145.0, t_bateria=130.0), cfg)
    assert nomes(sumiu) == ['bateria_perdida']


@pytest.mark.req('PAT-18')
def test_bateria_perdida_durante_o_dock_segue_encaixando(cfg):
    encaixando = estado(cfg, d.ENCAIXANDO, acao=d.DOCK, t_acao=100.0, tentativas_dock=1,
                        motivo_doca=d.POR_BATERIA)
    saida = d.decidir(encaixando, entrada(agora=125.0, t_bateria=110.0), cfg)
    assert nomes(saida) == ['bateria_perdida'] and saida.acoes == ()


@pytest.mark.req('PAT-18b')
def test_bateria_perdida_na_doca_encerra_com_3_sem_acao_nova(cfg):
    carregando = estado(cfg, d.CARREGANDO, motivo_doca=d.POR_BATERIA)
    saida = d.decidir(carregando, entrada(agora=121.0, t_bateria=110.0, na_base=True), cfg)
    assert nomes(saida) == ['bateria_perdida']
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_SEM_BATERIA),)


@pytest.mark.req('PAT-18')
@pytest.mark.req('PAT-18b')
def test_bateria_some_no_trecho_e_nao_volta_chega_a_doca_e_encerra_com_3(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0001, parar_bateria_em=20).rodar(200)
    assert mundo.codigo == d.CODIGO_SEM_BATERIA
    eventos = mundo.nomes()
    assert eventos.count('bateria_perdida') == 2  # uma no trecho, outra já na doca
    assert 'dock_ok' in eventos
    assert mundo.eventos[-1]['detalhe'] == 'na_doca'
    # Nenhum ponto de patrulha depois da perda.
    assert d.DESTINO not in mundo.acoes_enviadas()[mundo.acoes_enviadas().index(d.APROXIMACAO):]


# ---------------------------------------------------------------- limites relativos

def config_relativa(**bateria):
    return fazer_config(ambiente='gazebo', bateria={'modo': 'relativo', **bateria})


@pytest.mark.req('PAT-21')
@pytest.mark.req('PAT-21b')
def test_modo_relativo_calcula_os_limites_da_primeira_leitura_e_grava():
    cfg = config_relativa(alta=0.5, baixa=0.4, critica=0.3)  # ignorados no modo relativo
    mundo = Mundo(cfg, bateria=0.87, carga=0.0).rodar(2)
    primeiro = mundo.eventos[0]
    assert primeiro['evento'] == 'limites_bateria' and primeiro['b0'] == 0.87
    limites = mundo.estado.limites
    assert limites.alta == pytest.approx(0.865)
    assert limites.baixa == pytest.approx(0.86)
    assert limites.critica == pytest.approx(0.85)
    assert primeiro['limites'] == limites.como_dict()
    assert mundo.acoes_enviadas() == [d.UNDOCK]  # b0 já está acima de `alta`


@pytest.mark.req('PAT-21')
def test_modo_relativo_fixa_os_limites_ate_o_fim():
    cfg = config_relativa()
    mundo = Mundo(cfg, bateria=0.87, carga=0.0, descarga=0.001).rodar(8)
    fixados = mundo.estado.limites
    mundo.rodar(40)
    assert mundo.estado.limites == fixados
    assert mundo.nomes().count('limites_bateria') == 1
    assert 'bateria_baixa' in mundo.nomes()  # caiu 1 ponto e reagiu em segundos


@pytest.mark.req('VAL-04')
@pytest.mark.req('PAT-21b')
def test_modo_relativo_com_b0_invalido_grava_os_limites_e_encerra_com_2():
    for b0 in (math.nan, 0.015):  # NaN, ou tão baixa que `critica` ficaria negativa
        cfg = config_relativa()
        mundo = Mundo(cfg, bateria=b0, carga=0.0).rodar(5)
        assert mundo.codigo == d.CODIGO_CONFIG
        assert mundo.nomes() == ['limites_bateria', 'config_invalida']
        assert mundo.eventos[-1]['detalhe'] == 'limites_invalidos'
        assert mundo.acoes_enviadas() == [d.ENCERRAR]


# ---------------------------------------------------------------- relógio

@pytest.mark.req('PAT-22')
def test_sem_clock_desde_o_inicio_encerra_com_9_em_tempo_de_relogio(cfg):
    mundo = Mundo(cfg, usa_sim_time=True, relogio_ate=0).rodar(30)
    assert mundo.codigo == d.CODIGO_SEM_RELOGIO
    assert mundo.nomes() == ['sem_relogio']
    assert mundo.t == 12.0  # passa de 10 s de relógio contados da primeira chamada (t=1)


@pytest.mark.req('PAT-22')
def test_clock_que_para_no_meio_cancela_a_acao_e_encerra_com_9(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0, usa_sim_time=True, relogio_ate=15).rodar(60)
    assert mundo.codigo == d.CODIGO_SEM_RELOGIO
    assert mundo.acoes_enviadas()[-2:] == [d.CANCELAR, d.ENCERRAR]
    assert mundo.t == 26.0


@pytest.mark.req('PAT-22')
def test_sem_tempo_simulado_a_falta_de_clock_nao_importa(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0, usa_sim_time=False).rodar(60)
    assert mundo.codigo is None


def test_tempo_limite_so_conta_depois_do_primeiro_clock(cfg):
    """O relógio simulado pode começar num valor alto: isso não pode estourar nada."""
    inicio = d.decidir(d.Estado(), d.Entrada(parede=1000.0, agora=None, usa_sim_time=True), cfg)
    saida = d.decidir(inicio.estado, d.Entrada(parede=1001.0, agora=5000.0, usa_sim_time=True,
                                               parede_relogio=1001.0), cfg)
    assert saida.acoes == () and saida.estado.t_inicio == 5000.0


# ---------------------------------------------------------------- pedido de retorno à doca

def _resultado(acao, status=d.SUCESSO):
    return d.Resultado(acao, status, 4 if status == d.SUCESSO else 6)


@pytest.mark.req('PAT-23')
def test_pedido_na_ronda_cancela_o_destino_e_vai_a_aproximacao_sem_contar_falha(cfg):
    inicial = patrulhando(cfg, falhas_seguidas=1)
    saida = d.decidir(inicial, entrada(pedido_doca=True), cfg)
    assert nomes(saida) == ['doca_pedida', 'destino_cancelado', 'destino_enviado']
    assert acoes(saida) == [d.CANCELAR, d.APROXIMACAO]
    assert saida.eventos[0]['detalhe'] == d.PATRULHANDO
    assert saida.eventos[2]['detalhe'] == 'aproximacao_doca:comando'
    assert saida.estado.fase == d.INDO_DOCA and saida.estado.motivo_doca == d.POR_COMANDO
    assert saida.estado.falhas_seguidas == 1  # o cancelamento não é destino falho


@pytest.mark.req('PAT-23')
def test_pedido_na_ronda_termina_encaixado_com_codigo_0_sem_recarregar(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0001, pedido_doca_em=40).rodar(400)
    assert mundo.codigo == d.CODIGO_ENCERRADO
    nomes_ = mundo.nomes()
    assert nomes_.index('doca_pedida') < nomes_.index('dock_ok') < nomes_.index('encerrado')
    assert 'carga_completa' not in nomes_ and nomes_.count('undock_ok') == 1
    assert mundo.eventos[-1]['evento'] == 'encerrado'
    assert mundo.eventos[-1]['detalhe'] == 'voltar_doca'
    assert mundo.na_base is True
    # Reação em até 2 s do pedido (t=40) e nenhum destino de patrulha depois dele.
    envios = [t for t, acao in mundo.acoes if acao[0] == d.APROXIMACAO]
    assert envios and 40 <= envios[0] <= 42
    assert not [t for t, acao in mundo.acoes if acao[0] == d.DESTINO and t >= 40]


@pytest.mark.req('PAT-23')
def test_pedido_repetido_nao_grava_de_novo(cfg):
    primeira = d.decidir(patrulhando(cfg), entrada(pedido_doca=True), cfg)
    de_novo = d.decidir(primeira.estado, entrada(pedido_doca=True), cfg)
    assert de_novo.acoes == () and de_novo.eventos == ()


@pytest.mark.req('PAT-15')
def test_sinal_prevalece_sobre_o_pedido(cfg):
    saida = d.decidir(patrulhando(cfg), entrada(sinal=True, pedido_doca=True), cfg)
    assert nomes(saida) == ['encerrado']
    assert saida.acoes == ((d.CANCELAR,), (d.ENCERRAR, d.CODIGO_ENCERRADO))


def test_depois_de_encerrar_o_pedido_nao_faz_nada(cfg):
    fim = d.decidir(patrulhando(cfg), entrada(sinal=True), cfg)
    de_novo = d.decidir(fim.estado, entrada(pedido_doca=True), cfg)
    assert de_novo.acoes == () and de_novo.eventos == ()


@pytest.mark.req('PAT-23b')
@pytest.mark.parametrize('fase', [d.CARREGANDO, d.INICIANDO])
def test_pedido_na_doca_encerra_sem_enviar_acao(cfg, fase):
    saida = d.decidir(estado(cfg, fase), entrada(pedido_doca=True, na_base=True), cfg)
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_ENCERRADO),)
    assert nomes(saida) == ['doca_pedida', 'encerrado']
    assert saida.eventos[0]['detalhe'] == fase and saida.eventos[1]['detalhe'] == 'voltar_doca'


@pytest.mark.req('PAT-23b')
def test_pedido_com_o_robo_carregando_na_doca_encerra_com_0(cfg):
    mundo = Mundo(cfg, bateria=0.5, carga=0.001, pedido_doca_em=5).rodar(30)
    assert mundo.codigo == d.CODIGO_ENCERRADO
    assert mundo.acoes_enviadas() == [d.ENCERRAR]
    assert mundo.nomes() == ['doca_pedida', 'encerrado']


@pytest.mark.req('PAT-23b')
def test_pedido_sem_confirmacao_de_doca_nao_tem_efeito(cfg):
    fora = d.decidir(estado(cfg, d.INICIANDO), entrada(pedido_doca=True, na_base=False), cfg)
    assert nomes(fora) == ['fora_da_doca']  # vale o PAT-17
    assert fora.acoes == ((d.ENCERRAR, d.CODIGO_FORA_DA_DOCA),)
    sem_status = d.decidir(estado(cfg, d.INICIANDO),
                           entrada(pedido_doca=True, na_base=None, agora=10.0), cfg)
    assert sem_status.acoes == () and sem_status.eventos == ()


@pytest.mark.req('PAT-23c')
def test_pedido_durante_o_undock_fica_pendente(cfg):
    saindo = estado(cfg, d.SAINDO_DOCA, acao=d.UNDOCK, t_acao=100.0)
    espera = d.decidir(saindo, entrada(pedido_doca=True, na_base=True), cfg)
    assert espera.acoes == () and espera.eventos == ()
    assert espera.estado.fase == d.SAINDO_DOCA and espera.estado.acao == d.UNDOCK


@pytest.mark.req('PAT-23c')
def test_undock_ok_com_pedido_pendente_aplica_o_pedido(cfg):
    saindo = estado(cfg, d.SAINDO_DOCA, acao=d.UNDOCK, t_acao=100.0)
    saida = d.decidir(saindo, entrada(pedido_doca=True, na_base=False,
                                      resultado=_resultado(d.UNDOCK)), cfg)
    assert nomes(saida) == ['undock_ok', 'doca_pedida', 'destino_enviado']
    assert acoes(saida) == [d.APROXIMACAO]
    assert saida.estado.fase == d.INDO_DOCA and saida.estado.motivo_doca == d.POR_COMANDO


@pytest.mark.req('PAT-23c')
def test_undock_falho_com_pedido_pendente_vale_o_pat_16(cfg):
    saindo = estado(cfg, d.SAINDO_DOCA, acao=d.UNDOCK, t_acao=100.0)
    saida = d.decidir(saindo, entrada(pedido_doca=True, na_base=True,
                                      resultado=_resultado(d.UNDOCK, d.FALHOU)), cfg)
    assert nomes(saida) == ['undock_falhou']
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_UNDOCK),)


@pytest.mark.req('PAT-23d')
@pytest.mark.parametrize('fase, acao', [(d.INDO_DOCA, d.APROXIMACAO), (d.ENCAIXANDO, d.DOCK)])
def test_pedido_na_ida_por_bateria_troca_o_motivo_e_mantem_a_acao(cfg, fase, acao):
    ida = estado(cfg, fase, acao=acao, t_acao=100.0, motivo_doca=d.POR_BATERIA)
    saida = d.decidir(ida, entrada(pedido_doca=True), cfg)
    assert nomes(saida) == ['doca_pedida'] and saida.eventos[0]['detalhe'] == fase
    assert saida.acoes == () and saida.estado.acao == acao
    assert saida.estado.motivo_doca == d.POR_COMANDO
    de_novo = d.decidir(saida.estado, entrada(pedido_doca=True), cfg)
    assert de_novo.eventos == ()  # idempotente: o pedido é um nível, e não um evento


@pytest.mark.req('PAT-23d')
def test_dock_confirmado_depois_do_pedido_encerra_com_0_sem_carregar(cfg):
    ida = estado(cfg, d.ENCAIXANDO, acao=d.DOCK, t_acao=100.0, motivo_doca=d.POR_BATERIA)
    pedido = d.decidir(ida, entrada(pedido_doca=True), cfg)
    saida = d.decidir(pedido.estado, entrada(pedido_doca=True, na_base=True,
                                             resultado=_resultado(d.DOCK)), cfg)
    assert nomes(saida) == ['dock_ok', 'encerrado']
    assert saida.eventos[1]['detalhe'] == 'voltar_doca'
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_ENCERRADO),)


@pytest.mark.req('PAT-23d')
def test_pedido_durante_a_ida_por_bateria_ponta_a_ponta(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.02)
    mundo.rodar(400, ate=lambda m: 'bateria_baixa' in m.nomes())
    assert 'bateria_baixa' in mundo.nomes() and mundo.codigo is None
    mundo.pedido_doca_em = mundo.t + 1
    mundo.rodar(400)
    nomes_ = mundo.nomes()
    assert mundo.codigo == d.CODIGO_ENCERRADO
    assert nomes_.index('bateria_baixa') < nomes_.index('doca_pedida') < nomes_.index('dock_ok')
    assert 'carga_completa' not in nomes_


@pytest.mark.req('PAT-23d')
def test_pedido_depois_de_falhas_seguidas_mantem_o_codigo_7(cfg):
    ida = estado(cfg, d.ENCAIXANDO, acao=None, motivo_doca=d.POR_FALHAS, t_resultado_dock=109.0)
    saida = d.decidir(ida, entrada(pedido_doca=True, na_base=True), cfg)
    assert nomes(saida) == ['dock_ok', 'falhas_seguidas']  # sem doca_pedida
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_FALHAS),)


@pytest.mark.req('PAT-23')
def test_destino_falho_do_mesmo_ciclo_conta_e_o_pedido_prevalece_sobre_o_pat_08(cfg):
    inicial = patrulhando(cfg, falhas_seguidas=2)
    saida = d.decidir(inicial, entrada(pedido_doca=True,
                                       resultado=_resultado(d.DESTINO, d.FALHOU)), cfg)
    assert nomes(saida) == ['destino_falhou', 'doca_pedida', 'destino_enviado']
    assert saida.estado.falhas_seguidas == 3 and saida.estado.motivo_doca == d.POR_COMANDO


@pytest.mark.req('PAT-23')
def test_pedido_prevalece_sobre_a_bateria_baixa_e_a_critica(cfg):
    for bateria in (0.15, 0.05):  # abaixo de `baixa` e de `critica`
        saida = d.decidir(patrulhando(cfg), entrada(pedido_doca=True, bateria=bateria), cfg)
        assert nomes(saida) == ['doca_pedida', 'destino_cancelado', 'destino_enviado']
        assert saida.estado.motivo_doca == d.POR_COMANDO


@pytest.mark.req('PAT-23')
def test_dock_que_falha_depois_do_pedido_vale_o_pat_11(cfg):
    mundo = Mundo(cfg, bateria=0.99, descarga=0.0001, falhar_dock=99,
                  pedido_doca_em=40).rodar(600)
    assert mundo.codigo == d.CODIGO_DOCK
    assert 'doca_pedida' in mundo.nomes() and mundo.nomes()[-1] == 'dock_falhou'


@pytest.mark.req('PAT-23b')
def test_pedido_na_doca_prevalece_sobre_a_bateria_perdida(cfg):
    carregando = estado(cfg, d.CARREGANDO)
    saida = d.decidir(carregando, entrada(pedido_doca=True, na_base=True, agora=200.0,
                                          t_bateria=110.0), cfg)
    assert nomes(saida) == ['doca_pedida', 'encerrado']
    assert saida.acoes == ((d.ENCERRAR, d.CODIGO_ENCERRADO),)


@pytest.mark.req('PAT-23b')
def test_pedido_com_carregando_fora_da_doca_fica_pendente_e_reencaixa(cfg):
    carregando = estado(cfg, d.CARREGANDO)
    saida = d.decidir(carregando, entrada(pedido_doca=True, na_base=False), cfg)
    assert acoes(saida) == [d.APROXIMACAO] and saida.estado.fase == d.INDO_DOCA
    assert 'doca_pedida' not in nomes(saida)

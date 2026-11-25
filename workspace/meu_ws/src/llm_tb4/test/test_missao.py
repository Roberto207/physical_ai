"""Regras da execução, sem ROS: cada linha das tabelas do plano."""
from dataclasses import replace
from pathlib import Path

import pytest

from llm_tb4 import mapa, missao, pontos
from llm_tb4.interpretador import carregar_destinos
from llm_tb4.missao import (CANCELANDO, CONFIRMANDO, ENCAIXAR, ENVIANDO, EXECUTANDO, NAVEGAR,
                            PARADO, PREPARANDO, SAIR, TRAVADO, Aceite, Encerrar, Fim, Mensagem,
                            Ordem, Relogio, Sensores)

WORKSPACE = Path(__file__).resolve().parents[4]
ARQUIVO = WORKSPACE / 'patrulha_oficial' / 'patrol_loop.py'
DOCA, PONTOS = pontos.ler_pontos(ARQUIVO)
ROTA = pontos.Rota(DOCA, PONTOS, carregar_destinos())

PRONTO = Sensores(na_doca=False, doca_visivel=True, idade_doca=1.0, bateria=0.8,
                  idade_bateria=1.0, idade_tf=0.1,
                  prontos=frozenset({SAIR, NAVEGAR, ENCAIXAR}))
NA_DOCA = replace(PRONTO, na_doca=True)


def acao(nome, **argumentos):
    return {'acao': nome, 'argumentos': argumentos}


IR4 = acao('ir_para', local='ponto_4')
IR2 = acao('ir_para', local='ponto_2')


class Mundo:
    """Estado, relógio e ações acumuladas, para escrever cenários curtos."""

    def __init__(self, sensores=PRONTO, freio=False):
        self.cfg = missao.Config(freio, ROTA.destino, ROTA.aproximacao())
        self.s, self.t, self.acoes = sensores, 100.0, []
        self.e = missao.inicial(self.t)
        self.evento(Ordem(0, ''))          # fim do aquecimento do modelo

    def evento(self, evento, depois=0.0):
        self.t += depois
        self.e, novas = missao.decidir(self.e, evento, self.s, self.t, self.cfg)
        self.acoes += novas
        return novas

    def dizer(self, frase, parar=False):
        return self.evento(Mensagem(frase, parar))

    def responder(self, ordem_acao, epoca=None, depois=0.5):
        return self.evento(Ordem(epoca or self.e.epoca, 'frase', ordem_acao), depois)

    def pedir(self, ordem_acao):
        self.dizer('pedido')
        return self.responder(ordem_acao)

    def aceitar(self, ok=True):
        return self.evento(Aceite(self.e.seq, ok), 0.1)

    def terminar(self, ok=True):
        return self.evento(Fim(self.e.seq, ok), 1.0)

    def tique(self, depois=0.1):
        return self.evento(Relogio(), depois)

    def navegando(self, ordem_acao=IR4):
        self.pedir(ordem_acao)
        self.aceitar()
        assert self.e.fase == EXECUTANDO
        return self

    def enviados(self):
        return [a[2] for a in self.acoes if a[0] == 'enviar']

    def textos(self):
        return ' | '.join(a[2] for a in self.acoes if a[0] == 'log')


def tipos(acoes):
    return [a[0] for a in acoes if a[0] != 'log']


# ---------------------------------------------------------------- missões
def test_pontos_vem_da_patrulha_oficial_e_passam_no_mapa():
    conferir = mapa.verificador(WORKSPACE / 'mapas' / 'mapa_lab_novo.yaml')
    assert len(PONTOS) == 4 and ROTA.problemas(conferir) == []


def test_ponto_nomeado_usa_as_coordenadas_e_olha_o_seguinte():
    passo = ROTA.destino(IR4)
    assert (passo.x, passo.y) == PONTOS[3]
    assert passo.graus == pytest.approx(pontos.direcao(PONTOS[3], PONTOS[0]))


def test_coordenada_usa_a_direcao_pedida_ou_zero():
    assert ROTA.destino(acao('ir_para_coordenadas', x=-3.5, y=-3.0, graus=None)).graus == 0
    assert ROTA.destino(acao('ir_para_coordenadas', x=-3.5, y=-3.0, graus=90)).graus == 90


def test_perto_da_doca_e_recusado():
    conferir = ROTA.verificador(lambda x, y: None)
    assert 'perto_da_doca' in conferir(DOCA[0] + 0.3, DOCA[1])
    assert conferir(*PONTOS[0]) is None


@pytest.mark.parametrize('conteudo', ['', 'DOCA = 1', 'DOCA = (0, 0)\nPONTOS = ()', 'x = ('])
def test_arquivo_de_pontos_quebrado_e_recusado(tmp_path, conteudo):
    (tmp_path / 'p.py').write_text(conteudo)
    with pytest.raises(pontos.PontosInvalidos):
        pontos.ler_pontos(tmp_path / 'p.py')


def test_ir_estando_na_doca_sai_confirma_e_navega():
    m = Mundo(NA_DOCA)
    m.pedir(IR4)
    assert [p.tipo for p in m.enviados()] == [SAIR]
    m.aceitar()
    m.terminar()
    assert m.e.fase == CONFIRMANDO
    m.tique()
    assert m.e.fase == CONFIRMANDO          # a doca ainda consta como ocupada
    m.s = PRONTO
    m.tique()
    assert [p.tipo for p in m.enviados()] == [SAIR, NAVEGAR]
    m.aceitar()
    m.terminar()
    assert m.e.fase == PARADO and 'CONCLUIDO' in m.textos()


def test_voltar_para_base_aproxima_e_encaixa_mesmo_sem_bateria():
    m = Mundo(replace(PRONTO, bateria=0.05))
    m.pedir(acao('voltar_para_base'))
    m.aceitar()
    m.terminar()
    m.aceitar()
    assert [p.tipo for p in m.enviados()] == [NAVEGAR, ENCAIXAR]
    assert (m.enviados()[0].x, m.enviados()[0].y) == PONTOS[0]


@pytest.mark.parametrize('sensores, nome', [
    (NA_DOCA, 'voltar_para_base'), (NA_DOCA, 'encaixar'), (PRONTO, 'sair_da_base')])
def test_nada_a_fazer(sensores, nome):
    m = Mundo(sensores)
    m.pedir(acao(nome))
    assert m.e.fase == PARADO and not m.enviados() and 'nada a fazer' in m.textos()


# ---------------------------------------------------------------- pré-condições
@pytest.mark.parametrize('mudanca, motivo', [
    ({'idade_doca': 60.0}, 'recente da doca'),
    ({'bateria': 0.15}, 'abaixo de 20%'),
    ({'bateria': float('nan')}, 'bateria'),
    ({'idade_bateria': 100.0}, 'bateria'),
    ({'idade_tf': None}, 'map→odom'),
    ({'idade_tf': 5.0}, 'map→odom'),
    ({'prontos': frozenset()}, 'indisponível'),
    ({'meta_alheia': True}, 'outro programa')])
def test_nao_envia_sem_as_condicoes_e_desiste_no_prazo(mudanca, motivo):
    m = Mundo(replace(PRONTO, **mudanca))
    m.pedir(IR4)
    assert m.e.fase == PREPARANDO and not m.enviados()
    m.tique(missao.PRAZO_PREPARO_S + 1)
    assert m.e.fase == PARADO and not m.enviados() and motivo in m.textos()


def test_condicao_que_aparece_durante_a_espera_libera_o_envio():
    m = Mundo(replace(PRONTO, idade_tf=5.0))
    m.pedir(IR4)
    m.s = PRONTO
    m.tique()
    assert m.e.fase == ENVIANDO


def test_sair_da_doca_exige_localizacao_ja_recebida_mas_nao_recente():
    m = Mundo(replace(NA_DOCA, idade_tf=None))
    m.pedir(acao('sair_da_base'))
    assert not m.enviados()
    m = Mundo(replace(NA_DOCA, idade_tf=300.0))
    m.pedir(acao('sair_da_base'))
    assert [p.tipo for p in m.enviados()] == [SAIR]


def test_encaixar_exige_doca_visivel():
    m = Mundo(replace(PRONTO, doca_visivel=False))
    m.pedir(acao('encaixar'))
    m.tique(missao.PRAZO_PREPARO_S + 1)
    assert not m.enviados() and 'visível' in m.textos()


def test_doca_desconhecida_recusa():
    m = Mundo(Sensores())
    m.pedir(IR4)
    assert m.e.fase == PARADO and 'desconhecido' in m.textos()


# ---------------------------------------------------------------- interrupções no trajeto
def test_mensagem_no_trajeto_cancela_na_chegada_e_vira_a_ordem():
    m = Mundo().navegando()
    novas = m.dizer('vai pra geladeira')
    assert tipos(novas) == ['cancelar', 'interpretar'] and m.e.fase == CANCELANDO
    m.responder(IR2)
    assert len(m.enviados()) == 1               # nada novo antes de o cancelamento confirmar
    m.terminar(False)
    assert (m.enviados()[-1].x, m.enviados()[-1].y) == PONTOS[1]


def test_ordem_que_chega_depois_do_cancelamento_tambem_vale():
    m = Mundo().navegando()
    m.dizer('vai pra geladeira')
    m.terminar(False)
    assert m.e.fase == PARADO and missao.aceita_mensagem(m.e)
    m.responder(IR2)
    assert len(m.enviados()) == 2


def test_mensagem_sem_comando_cancela_e_deixa_parado():
    m = Mundo().navegando()
    m.dizer('breca')
    m.responder(None)
    m.terminar(False)
    assert m.e.fase == PARADO and len(m.enviados()) == 1


def test_duas_mensagens_seguidas_vale_a_ultima():
    m = Mundo().navegando()
    m.dizer('vai pra geladeira')
    primeira = m.e.epoca
    m.dizer('vai pra porta')
    m.responder(IR2, epoca=primeira)
    assert 'DESCARTADO' in m.textos()
    m.terminar(False)
    m.responder(acao('ir_para', local='ponto_3'))
    assert (m.enviados()[-1].x, m.enviados()[-1].y) == PONTOS[2] and len(m.enviados()) == 2


def test_ordem_guardada_e_apagada_por_mensagem_mais_nova():
    m = Mundo().navegando()
    m.dizer('a')
    m.responder(IR2)
    m.dizer('b')
    m.terminar(False)
    assert len(m.enviados()) == 1


def test_parar_cancela_apaga_pendente_e_cancela_tudo():
    m = Mundo().navegando()
    m.dizer('a')
    m.responder(IR2)
    novas = m.dizer('pare', parar=True)
    assert 'cancelar_tudo' in tipos(novas)
    m.terminar(False)
    assert m.e.fase == PARADO and len(m.enviados()) == 1


def test_parar_durante_a_interpretacao_descarta_o_resultado():
    m = Mundo()
    m.dizer('vai pra janela')
    epoca = m.e.epoca
    m.dizer('pare', parar=True)
    m.responder(IR4, epoca=epoca)
    assert not m.enviados() and 'DESCARTADO' in m.textos()


def test_modelo_respondendo_parar_tambem_para():
    m = Mundo().navegando()
    m.dizer('encerra por aqui')
    novas = m.responder(acao('parar'))
    assert 'cancelar_tudo' in tipos(novas)


def test_parado_interpretando_ignora_outras_mensagens():
    m = Mundo()
    m.dizer('vai pra janela')
    assert not missao.aceita_mensagem(m.e)
    assert tipos(m.dizer('vai pra porta')) == [] and 'OCUPADO' in m.textos()


def test_aquecendo_o_modelo_ignora_pedidos_mas_atende_parar():
    cfg = missao.Config(False, ROTA.destino, ROTA.aproximacao())
    e = missao.inicial(0)
    e, acoes = missao.decidir(e, Mensagem('vai', False), PRONTO, 1, cfg)
    assert tipos(acoes) == []
    e, acoes = missao.decidir(e, Mensagem('pare', True), PRONTO, 2, cfg)
    assert 'cancelar_tudo' in tipos(acoes)


# ---------------------------------------------------------------- dock e saída da doca
@pytest.mark.parametrize('sensores, nome', [(NA_DOCA, 'sair_da_base'), (PRONTO, 'encaixar')])
def test_manobra_termina_e_a_ultima_mensagem_e_obedecida(sensores, nome):
    m = Mundo(sensores)
    m.pedir(acao(nome))
    m.aceitar()
    assert 'cancelar' not in tipos(m.dizer('vai pra geladeira'))
    m.responder(IR2)
    m.terminar()
    m.s = replace(PRONTO, na_doca=nome == 'encaixar')
    m.tique()
    if nome == 'encaixar':                      # encaixou: para ir, sai de novo
        assert m.enviados()[-1].tipo == SAIR
    else:
        assert (m.enviados()[-1].x, m.enviados()[-1].y) == PONTOS[1]


def test_mensagem_na_saida_descarta_o_resto_da_missao():
    m = Mundo(NA_DOCA)
    m.pedir(IR4)
    m.aceitar()
    m.dizer('breca')
    m.responder(None)
    m.terminar()
    m.s = PRONTO
    m.tique()
    assert m.e.fase == PARADO and [p.tipo for p in m.enviados()] == [SAIR]


@pytest.mark.parametrize('sensores, nome', [(NA_DOCA, 'sair_da_base'), (PRONTO, 'encaixar')])
def test_parar_cancela_a_manobra(sensores, nome):
    m = Mundo(sensores)
    m.pedir(acao(nome))
    m.aceitar()
    assert 'cancelar' in tipos(m.dizer('pare', parar=True)) and m.e.fase == CANCELANDO


def test_doca_nao_confirmada_interrompe():
    m = Mundo(NA_DOCA)
    m.pedir(IR4)
    m.aceitar()
    m.terminar()
    m.tique(missao.PRAZO_CONFIRMAR_S + 1)
    assert m.e.fase == PARADO and len(m.enviados()) == 1 and 'não confirmada' in m.textos()


# ---------------------------------------------------------------- respostas do servidor
def test_recusa_depois_de_um_sucesso_nao_vira_sucesso():
    m = Mundo().navegando()
    m.terminar()
    m.pedir(IR2)
    m.aceitar(False)
    assert m.e.fase == PARADO and 'recusada' in m.textos()


def test_resultado_de_meta_antiga_e_ignorado():
    m = Mundo().navegando()
    antiga = m.e.seq
    m.dizer('a')
    m.responder(IR2)
    m.terminar(False)
    m.aceitar()
    m.evento(Fim(antiga, True))
    assert m.e.fase == EXECUTANDO


def test_parar_antes_do_aceite_cancela_quando_ele_chega():
    m = Mundo()
    m.pedir(IR4)
    m.dizer('pare', parar=True)
    assert m.e.fase == CANCELANDO
    assert ('cancelar', m.e.seq) in m.aceitar()


def test_aceite_atrasado_de_meta_antiga_e_cancelado():
    m = Mundo().navegando()
    assert m.evento(Aceite(m.e.seq - 1, True)) == [('cancelar', m.e.seq - 1)]


def test_falha_na_navegacao_interrompe_a_missao():
    m = Mundo(PRONTO).navegando(acao('voltar_para_base'))
    m.terminar(False)
    assert m.e.fase == PARADO and [p.tipo for p in m.enviados()] == [NAVEGAR]


# ---------------------------------------------------------------- prazos e perdas
def test_sem_aceite_trava_e_so_sai_com_confirmacao():
    m = Mundo()
    m.pedir(IR4)
    novas = m.tique(missao.PRAZO_ACEITE_S + 1)
    assert m.e.fase == TRAVADO and 'cancelar_tudo' in tipos(novas)
    m.pedir(IR2)
    assert len(m.enviados()) == 1 and 'não foi confirmado' in m.textos()
    m.terminar(False)
    assert m.e.fase == PARADO


def test_cancelamento_sem_resposta_trava_e_parar_repete():
    m = Mundo().navegando()
    m.dizer('pare', parar=True)
    m.tique(missao.PRAZO_CANCELAR_S + 1)
    assert m.e.fase == TRAVADO
    assert 'cancelar' in tipos(m.dizer('pare', parar=True))


@pytest.mark.parametrize('mudanca, depois', [
    ({}, missao.PRAZO_NAVEGAR_S + 1), ({'idade_tf': 30.0}, 1), ({'idade_doca': 60.0}, 1)])
def test_prazo_ou_perda_de_sensor_cancela(mudanca, depois):
    m = Mundo().navegando()
    m.s = replace(PRONTO, **mudanca)
    assert 'cancelar' in tipos(m.tique(depois)) and m.e.fase == CANCELANDO


def test_bateria_baixa_no_trajeto_so_avisa_uma_vez():
    m = Mundo().navegando()
    m.s = replace(PRONTO, bateria=0.1)
    m.tique()
    m.tique()
    assert m.e.fase == EXECUTANDO and m.textos().count('BATERIA BAIXA') == 1


def test_interpretacao_velha_nao_move():
    m = Mundo()
    m.dizer('vai pra janela')
    m.responder(IR4, depois=missao.VALIDADE_INTERPRETACAO_S + 1)
    assert not m.enviados() and 'demorou' in m.textos()


# ---------------------------------------------------------------- freio e encerramento
def test_com_o_freio_nada_e_enviado_nem_cancelado():
    m = Mundo(freio=True)
    m.pedir(IR4)
    m.dizer('pare', parar=True)
    assert not [a for a in m.acoes if a[0] in ('enviar', 'cancelar', 'cancelar_tudo')]


@pytest.mark.parametrize('sensores, ordem_acao', [(PRONTO, IR4), (NA_DOCA, IR4)])
def test_encerrar_cancela_a_meta_ativa_inclusive_manobra(sensores, ordem_acao):
    m = Mundo(sensores)
    m.pedir(ordem_acao)
    m.aceitar()
    novas = m.evento(Encerrar())
    assert tipos(novas) == ['cancelar', 'cancelar_tudo']


def test_encerrar_parado_nao_cancela_metas_dos_outros():
    assert tipos(Mundo().evento(Encerrar())) == []

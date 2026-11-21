"""O pedido de undock não pode ser marcado como rejeitado por demorar 2 s."""
from types import SimpleNamespace

from action_msgs.msg import GoalStatus

from patrulha_tb4 import decisao
from patrulha_tb4.no_patrulha import Patrulha


class Futuro:
    def __init__(self):
        self.valor = None

    def done(self):
        return self.valor is not None

    def result(self):
        return self.valor


class Cliente:
    def __init__(self, futuro):
        self.futuro = futuro

    def send_goal_async(self, _pedido):
        return self.futuro


def test_undock_aguarda_aceitacao_sem_rejeicao_falsa(monkeypatch):
    monkeypatch.setattr(
        'patrulha_tb4.no_patrulha.rclpy.spin_until_future_complete',
        lambda *_args, **_kwargs: None)
    pedido, resultado = Futuro(), Futuro()
    patrulha = object.__new__(Patrulha)
    patrulha.nav = object()
    patrulha._ativa = patrulha._rejeitada = None
    patrulha._futuro_envio = patrulha._futuro_base = patrulha._meta_base = None

    patrulha._enviar_base(decisao.UNDOCK, Cliente(pedido), object())
    assert patrulha._colher_resultado() is None
    assert patrulha._colher_resultado() is None
    pedido.valor = SimpleNamespace(accepted=True, get_result_async=lambda: resultado)
    assert patrulha._colher_resultado() is None
    resultado.valor = SimpleNamespace(status=GoalStatus.STATUS_SUCCEEDED)
    recebido = patrulha._colher_resultado()
    assert recebido.acao == decisao.UNDOCK
    assert recebido.status == decisao.SUCESSO


def test_undock_rejeicao_real(monkeypatch):
    monkeypatch.setattr(
        'patrulha_tb4.no_patrulha.rclpy.spin_until_future_complete',
        lambda *_args, **_kwargs: None)
    pedido = Futuro()
    patrulha = object.__new__(Patrulha)
    patrulha.nav = object()
    patrulha._ativa = patrulha._rejeitada = None
    patrulha._futuro_envio = patrulha._futuro_base = patrulha._meta_base = None

    patrulha._enviar_base(decisao.UNDOCK, Cliente(pedido), object())
    pedido.valor = SimpleNamespace(accepted=False)
    recebido = patrulha._colher_resultado()
    assert recebido.status == decisao.FALHOU
    assert recebido.codigo == 'rejeitado'

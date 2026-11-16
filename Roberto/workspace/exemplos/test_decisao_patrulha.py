import pytest

from decisao_patrulha import decidir


@pytest.mark.parametrize('bateria, na_base, esperado', [
    (None, False, 'aguardar'),
    (None, True, 'aguardar'),
    (0.50, True, 'carregar'),
    (0.95, True, 'sair_da_base'),
    (0.50, False, 'patrulhar'),
    (0.19, False, 'ir_carregar'),
    (0.09, False, 'parar'),
    (0.05, True, 'carregar'),  # na base, bateria crítica não é motivo para parar
])
def test_decidir(bateria, na_base, esperado):
    assert decidir(bateria, na_base) == esperado

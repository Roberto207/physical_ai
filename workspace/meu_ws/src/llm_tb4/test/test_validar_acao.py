import pytest

from llm_tb4.validar_acao import validar

LOCAIS = {'lab': [1.0, 2.0], 'corredor': [-3.0, 0.5]}


@pytest.mark.parametrize('acao, bateria, permitido', [
    ({'acao': 'ir_para', 'argumentos': {'local': 'lab'}}, 0.8, True),
    ({'acao': 'voltar_para_base'}, 0.05, True),  # voltar e parar valem com bateria baixa
    ({'acao': 'parar'}, None, True),
    ({'acao': 'ir_para', 'argumentos': {'local': 'lua'}}, 0.8, False),
    ({'acao': 'ir_para', 'argumentos': {'local': 'lab'}}, 0.1, False),
    ({'acao': 'ir_para', 'argumentos': {'local': 'lab'}}, None, False),
    ({'acao': 'ir_para', 'argumentos': {}}, 0.8, False),
    ({'acao': 'ir_para', 'argumentos': {'local': 'lab', 'velocidade': 9}}, 0.8, False),
    ({'acao': 'ir_para', 'argumentos': 'lab'}, 0.8, False),
    ({'acao': 'exec', 'argumentos': {'codigo': 'import os'}}, 0.8, False),
    ('vá até o lab', 0.8, False),
])
def test_validar(acao, bateria, permitido):
    assert validar(acao, LOCAIS, bateria)[0] is permitido

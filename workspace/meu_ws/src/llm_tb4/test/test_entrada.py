import pytest

from llm_tb4.entrada import limpar


def teclado(dados):
    """O que o input() entrega para esses bytes, com o tratamento de erro do terminal."""
    return dados.decode('utf-8', 'surrogateescape')


@pytest.mark.parametrize('dados, esperado', [
    ('vá para a geladeira'.encode(), 'vá para a geladeira'),
    (b'v\xc3\xa1 para a g\xc3eladeira', 'vá para a geladeira'),  # sobra de um Backspace
    (b'pare\xc3', 'pare'),
    (b'\xc3', ''),  # só o byte solto: o falar trata como linha vazia, que é "pare"
])
def test_limpar(dados, esperado):
    assert limpar(teclado(dados)) == esperado


def test_resultado_pode_ser_publicado():
    limpar(teclado(b'v\xc3 ao ponto 1\xa1')).encode('utf-8')  # não pode levantar erro

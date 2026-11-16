"""Exemplo: a decisão da patrulha, sem ROS e sem robô.

Como é uma função pura, dá para testar cada situação em milissegundos, inclusive as
difíceis de provocar num simulador. O nó ROS só lê os sensores, chama decidir() e executa.
"""
BATERIA_ALTA = 0.95
BATERIA_BAIXA = 0.20
BATERIA_CRITICA = 0.10


def decidir(bateria, na_base):
    """Devolve o próximo passo. bateria é uma fração de 0 a 1, ou None se ainda não chegou."""
    if bateria is None:
        return 'aguardar'  # o patrol_loop oficial quebra aqui: a variável ainda não existe
    if na_base:
        return 'carregar' if bateria < BATERIA_ALTA else 'sair_da_base'
    if bateria < BATERIA_CRITICA:
        return 'parar'
    if bateria < BATERIA_BAIXA:
        return 'ir_carregar'
    return 'patrulhar'

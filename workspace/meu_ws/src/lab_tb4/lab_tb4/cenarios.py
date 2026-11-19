"""Lê os cenários do L1 (config/cenarios_l1.yaml). Python puro, sem ROS (SIM-04, SIM-04b).

Usado pelo l1.launch.py (dentro do container) e pelo teste_l1.sh (no host, para validar o nome
do cenário antes de subir qualquer container):

    python3 cenarios.py <arquivo.yaml> nomes          lista os nomes, um por linha
    python3 cenarios.py <arquivo.yaml> tem <nome>     sai com 0 se o cenário existe
"""
import sys

import yaml

CAMPOS = ('config', 'base', 'limite_s', 'subir_nav2', 'subir_base', 'nav2_extra',
          'patrulha_extra', 'sinal_no_fim')


class CenarioInvalido(Exception):
    pass


def carregar(caminho):
    """{nome: cenário completo}, com os campos que faltarem vindos de `padrao`."""
    with open(caminho, 'r', encoding='utf-8') as arquivo:
        dados = yaml.safe_load(arquivo)
    padrao = dados.get('padrao') or {}
    faltando = [c for c in CAMPOS if c not in padrao]
    if faltando:
        raise CenarioInvalido(f'faltam no padrao: {", ".join(faltando)}')
    cenarios = {}
    for nome, proprio in (dados.get('cenarios') or {}).items():
        proprio = proprio or {}
        desconhecidos = sorted(set(proprio) - set(CAMPOS))
        if desconhecidos:
            raise CenarioInvalido(f'{nome}: campos desconhecidos {desconhecidos}')
        cenarios[nome] = {campo: proprio.get(campo, padrao[campo]) for campo in CAMPOS}
    return cenarios


def argumentos_launch(texto):
    """'a:=1 b:=x' -> [('a', '1'), ('b', 'x')], para os launch_arguments de um include."""
    pares = []
    for item in (texto or '').split():
        nome, separador, valor = item.partition(':=')
        if not separador or not nome:
            raise CenarioInvalido(f'argumento de launch inválido: {item!r} (use nome:=valor)')
        pares.append((nome, valor))
    return pares


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cenarios = carregar(argv[0])
    if argv[1] == 'nomes':
        print('\n'.join(cenarios))
        return 0
    if argv[1] == 'tem' and len(argv) > 2:
        return 0 if argv[2] in cenarios else 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

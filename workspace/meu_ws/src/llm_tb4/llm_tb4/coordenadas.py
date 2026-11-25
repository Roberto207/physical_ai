"""Lê coordenadas e direção de um pedido, por código. O modelo não extrai números."""
import re

NUMERO = r'-?\d+(?:[.,]\d+)?'
COM_PONTO = r'-?\d+(?:\.\d+)?'
MARCADOR = re.compile(r'coordenada|posicao|posição|\(')
UNIDADE = re.compile(r'\b(metros?|cm|graus|horas?|minutos?|segundos?|vezes)\b')
# Convenção do TurtleBot4Directions (turtlebot4_navigation): graus no referencial do mapa.
DIRECOES = {'nordeste': 315, 'noroeste': 45, 'sudeste': 225, 'sudoeste': 135,
            'norte': 0, 'oeste': 90, 'sul': 180, 'leste': 270}


def _valor(texto):
    return float(texto.replace(',', '.'))


def ler_coordenadas(frase):
    """Devolve (x, y) ou None. Formatos ambíguos ("1,5" sozinho) não são aceitos."""
    texto = frase.lower().replace('−', '-')
    achado = re.search(rf'\bx\s*[=:]?\s*({NUMERO})\s*[,;]?\s*'
                       rf'(?:e\s+)?\by\s*[=:]?\s*({NUMERO})', texto)
    if achado:
        resto = texto[:achado.start()] + texto[achado.end():]
        return None if re.search(r'\d', resto) else (_valor(achado[1]), _valor(achado[2]))
    marcado = bool(MARCADOR.search(texto))
    padroes = ((rf'({NUMERO})\s*;\s*({NUMERO})', False),
               (rf'({COM_PONTO}),\s+({COM_PONTO})', False),
               (rf'({NUMERO})\s+(?:e\s+)?({NUMERO})', False),
               (r'(-?\d+),(-?\d+)', True))
    for padrao, so_marcado in padroes:
        achado = re.search(rf'(?<![\d.,]){padrao}(?!\d|[.,]\d)', texto)
        if not achado or (so_marcado and not marcado):
            continue
        # Sem a palavra "coordenada", "posição" ou parênteses, os dois números precisam ter
        # sinal ou casa decimal: "entre 2 e 3" não é uma coordenada.
        if not marcado and not all(re.search(r'[-.,]', n) for n in achado.groups()):
            continue
        resto = texto[:achado.start()] + texto[achado.end():]
        if re.search(r'\d', resto) or UNIDADE.search(resto):
            return None
        return _valor(achado[1]), _valor(achado[2])
    return None


def ler_direcao(frase):
    """Graus pedidos ("virado para o leste") ou None."""
    texto = frase.lower()
    achadas = [graus for nome, graus in DIRECOES.items() if re.search(rf'\b{nome}\b', texto)]
    return achadas[0] if len(achadas) == 1 else None

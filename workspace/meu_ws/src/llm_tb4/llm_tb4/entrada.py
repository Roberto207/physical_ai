"""Limpeza do texto digitado no terminal. Sem ROS, para ser testável."""


def limpar(linha):
    """Devolve a linha sem os bytes que não formam um caractere UTF-8 completo.

    O Python entrega cada byte inválido do teclado como um "surrogate" (U+DC80 a U+DCFF), e o
    ROS se recusa a publicá-lo (UnicodeEncodeError, 2026-11-25, no robô). Acontece quando o
    Backspace apaga só um dos dois bytes de uma letra acentuada, em um terminal sem `stty
    iutf8`. Recodificar devolve os bytes originais: as letras completas voltam a ser texto, e
    o byte solto, que a pessoa quis apagar, é descartado.
    """
    return linha.encode('utf-8', 'surrogateescape').decode('utf-8', 'ignore')

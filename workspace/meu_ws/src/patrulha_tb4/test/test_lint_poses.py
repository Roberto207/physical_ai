"""TST-07 (prova do PAT-01): nenhuma pose escrita no código, só na configuração.

Falha se algum arquivo do pacote (fora de `test/`) chamar `getPoseStamped` ou montar uma
pose com números literais.
"""
import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PASTAS = [RAIZ / 'patrulha_tb4', RAIZ / 'launch']

# Construtores de pose: os das mensagens do ROS e o da nossa configuração.
CONSTRUTORES = {'Pose', 'PoseStamped', 'PoseWithCovarianceStamped', 'Point', 'Quaternion'}
# Atributos que, juntos, só existem em poses: `pose.position.x`, `pose.orientation.w`.
PARTES = {'position', 'orientation'}
COORDENADAS = {'x', 'y', 'z', 'w'}


def _numero_literal(no):
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.USub, ast.UAdd)):
        no = no.operand
    return isinstance(no, ast.Constant) and isinstance(no.value, (int, float)) \
        and not isinstance(no.value, bool)


def _nome(no):
    if isinstance(no, ast.Name):
        return no.id
    if isinstance(no, ast.Attribute):
        return no.attr
    return None


def problemas_em(codigo, arquivo='<texto>'):
    achados = []
    for no in ast.walk(ast.parse(codigo)):
        if isinstance(no, ast.Call):
            nome = _nome(no.func)
            if nome == 'getPoseStamped':
                achados.append(f'{arquivo}:{no.lineno}: chamada a getPoseStamped')
            elif nome in CONSTRUTORES:
                argumentos = list(no.args) + [chave.value for chave in no.keywords]
                if any(_numero_literal(arg) for arg in argumentos):
                    achados.append(f'{arquivo}:{no.lineno}: {nome}(...) com número literal')
        elif isinstance(no, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
            for alvo in alvos:
                e_coordenada = (isinstance(alvo, ast.Attribute) and alvo.attr in COORDENADAS
                                and isinstance(alvo.value, ast.Attribute)
                                and alvo.value.attr in PARTES)
                if e_coordenada and no.value is not None and _numero_literal(no.value):
                    achados.append(f'{arquivo}:{no.lineno}: coordenada de pose com número literal')
    return achados


@pytest.mark.req('PAT-01')
def test_nenhum_arquivo_do_pacote_escreve_pose_no_codigo():
    arquivos = [arquivo for pasta in PASTAS for arquivo in sorted(pasta.glob('*.py'))]
    assert len(arquivos) >= 5, 'o lint não achou os arquivos do pacote'
    achados = []
    for arquivo in arquivos:
        achados += problemas_em(arquivo.read_text(), arquivo.relative_to(RAIZ))
    assert achados == []


@pytest.mark.req('PAT-01')
@pytest.mark.parametrize('codigo', [
    'ponto = navigator.getPoseStamped([-5.0, 1.0], TurtleBot4Directions.EAST)',
    'p = Point(x=1.0, y=2.0)',
    'p = Pose("doca", 0.0, 1.0, 90)',
    'q = Quaternion(w=1.0)',
    'msg.pose.position.x = -5.0',
    'msg.pose.pose.orientation.w = 1',
])
def test_o_lint_pega_cada_jeito_de_escrever_uma_pose(codigo):
    assert problemas_em(codigo) != []


@pytest.mark.req('PAT-01')
@pytest.mark.parametrize('codigo', [
    'msg.pose.position.x = pose.x',
    'msg.pose.orientation.z = math.sin(meio)',
    'p = Pose(nome, *valores)',
    'limites = Limites(alta=0.95, baixa=0.20, critica=0.10)',
    'self.x = 0.0',
])
def test_o_lint_nao_acusa_o_que_vem_da_configuracao(codigo):
    assert problemas_em(codigo) == []

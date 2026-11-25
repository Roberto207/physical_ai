"""Onde ficam o prompt e os destinos: na árvore do código ou, compilado, em share/llm_tb4."""
from pathlib import Path


def caminho(*partes):
    no_codigo = Path(__file__).resolve().parent.parent.joinpath(*partes)
    if no_codigo.exists():
        return no_codigo
    from ament_index_python.packages import get_package_share_directory   # só dentro do ROS
    return Path(get_package_share_directory('llm_tb4')).joinpath(*partes)

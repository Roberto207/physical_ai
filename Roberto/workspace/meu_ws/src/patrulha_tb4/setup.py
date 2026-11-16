from glob import glob

from setuptools import setup

pacote = 'patrulha_tb4'

setup(
    name=pacote,
    version='0.1.0',
    packages=[pacote],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + pacote]),
        ('share/' + pacote, ['package.xml']),
        ('share/' + pacote + '/launch', glob('launch/*.launch.py')),
        ('share/' + pacote + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Equipe Physical AI (INF-UFG)',
    maintainer_email='nao-informado@example.com',
    description='Patrulha do TurtleBot 4 com volta à doca por bateria.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'patrulha = patrulha_tb4.no_patrulha:main',
            'validar_pontos = patrulha_tb4.pontos:main',
        ],
    },
)

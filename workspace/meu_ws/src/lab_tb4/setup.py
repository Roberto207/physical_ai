from glob import glob

from setuptools import setup

pacote = 'lab_tb4'

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
    description='Bringup dos ambientes do TurtleBot 4 do projeto (spec specs/migracao-humble).',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'base_falsa = lab_tb4.base_falsa:main',
            'vigia_l1 = lab_tb4.vigia_l1:main',
        ],
    },
)

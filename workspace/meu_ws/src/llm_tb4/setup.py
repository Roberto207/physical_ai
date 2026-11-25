from glob import glob

from setuptools import setup

pacote = 'llm_tb4'

setup(
    name=pacote,
    version='0.1.0',
    packages=[pacote],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + pacote]),
        ('share/' + pacote, ['package.xml']),
        ('share/' + pacote + '/launch', glob('launch/*_launch.py')),
        ('share/' + pacote + '/prompts', glob('prompts/*.txt')),
        ('share/' + pacote + '/config', glob('config/*.json')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Equipe Physical AI (INF-UFG)',
    maintainer_email='nao-informado@example.com',
    description='Linguagem natural para o TurtleBot 4 com um LLM local.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'natural_language_nav = llm_tb4.no_linguagem_natural:main',
        ],
    },
)

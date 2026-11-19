"""Log JSONL da patrulha, com o evento de início e o resumo final (OBS-01 a OBS-03). Sem ROS.

Uma linha JSON por evento. A lista de eventos é fechada: gravar um nome fora dela é
erro de programação, e não um evento novo.
"""
import hashlib
import json
import os
import time
from pathlib import Path

EVENTOS = (
    'inicio', 'limites_bateria', 'config_invalida', 'sem_bateria', 'fora_da_doca',
    'servidor_indisponivel', 'undock_ok', 'undock_falhou', 'destino_enviado', 'destino_ok',
    'destino_falhou', 'destino_cancelado', 'bateria_baixa', 'bateria_critica',
    'bateria_perdida', 'sem_relogio', 'dock_ok', 'dock_nao_confirmado', 'dock_falhou',
    'carga_completa', 'falhas_seguidas', 'doca_pedida', 'encerrado', 'resumo',
)

ESTADOS = ('iniciando', 'saindo_doca', 'patrulhando', 'indo_doca', 'encaixando',
           'carregando', 'encerrando')

CAMPOS_OPCIONAIS = ('ponto', 'resultado', 'detalhe')
CAMPOS_DE_INICIO = ('hash_codigo', 'hash_config', 'versao', 'ambiente', 'modelo')
CAMPOS_DE_LIMITES = ('b0', 'limites')
CAMPOS_DE_RESUMO = ('voltas', 'destinos_falhos', 'docks_confirmados', 'tentativas_dock',
                    'bateria_minima', 'duracao_s', 'codigo_saida')


def hash_codigo(pastas):
    """SHA-256 dos arquivos .py do pacote (OBS-03), sem `config/` e sem caches.

    `pastas` é uma lista de (rótulo, pasta). O rótulo entra na conta no lugar do caminho
    real, para o hash ser o mesmo no código-fonte e no pacote instalado.
    """
    resumo = hashlib.sha256()
    for rotulo, pasta in pastas:
        for arquivo in sorted(Path(pasta).glob('*.py')):
            resumo.update(f'{rotulo}/{arquivo.name}\n'.encode())
            resumo.update(arquivo.read_bytes())
    return resumo.hexdigest()


class Registro:
    """Grava os eventos e acumula os números do resumo."""

    def __init__(self, caminho, relogio_parede=time.time):
        self.caminho = str(caminho)
        os.makedirs(os.path.dirname(self.caminho) or '.', exist_ok=True)
        self._arquivo = open(self.caminho, 'a', encoding='utf-8')
        self._relogio_parede = relogio_parede
        self._parede_inicio = relogio_parede()
        self._primeiro = True
        self.resumo_gravado = False
        self.destinos_falhos = 0
        self.docks_confirmados = 0
        self.tentativas_dock = 0
        self.bateria_minima = None

    def observar_bateria(self, bateria):
        """Guarda a menor bateria vista, para o resumo."""
        if bateria is None or bateria != bateria:  # NaN não entra
            return
        if self.bateria_minima is None or bateria < self.bateria_minima:
            self.bateria_minima = bateria

    def gravar(self, evento, estado, bateria, t, **campos):
        if evento not in EVENTOS:
            raise ValueError(f'evento fora da lista fechada: {evento}')
        if estado not in ESTADOS:
            raise ValueError(f'estado desconhecido: {estado}')
        if self._primeiro and evento != 'inicio':
            raise ValueError('o primeiro evento precisa ser "inicio" (OBS-03)')
        permitidos = CAMPOS_OPCIONAIS
        if evento == 'inicio':
            permitidos += CAMPOS_DE_INICIO
            faltando = [campo for campo in CAMPOS_DE_INICIO if campo not in campos]
            if faltando:
                raise ValueError(f'faltam campos no evento inicio: {faltando}')
        elif evento == 'limites_bateria':
            permitidos += CAMPOS_DE_LIMITES
        elif evento == 'resumo':
            permitidos += CAMPOS_DE_RESUMO
        estranhos = [campo for campo in campos if campo not in permitidos]
        if estranhos:
            raise ValueError(f'campos fora do esquema em {evento}: {estranhos}')

        self.observar_bateria(bateria)
        if evento == 'destino_falhou':
            self.destinos_falhos += 1
        elif evento == 'dock_ok':
            self.docks_confirmados += 1
            self.tentativas_dock += 1
        elif evento == 'dock_nao_confirmado':
            self.tentativas_dock += 1

        linha = {'t': t, 't_parede': self._relogio_parede(), 'evento': evento,
                 'estado': estado, 'bateria': bateria}
        # No resumo, um campo sem valor (a bateria mínima, se nunca chegou) fica como null.
        linha.update({campo: valor for campo, valor in campos.items()
                      if valor is not None or evento == 'resumo'})
        self._arquivo.write(json.dumps(linha, ensure_ascii=False) + '\n')
        self._arquivo.flush()
        os.fsync(self._arquivo.fileno())
        self._primeiro = False

    def gravar_resumo(self, estado, bateria, t, voltas, codigo_saida):
        """OBS-02: uma vez só, em qualquer encerramento com código da tabela."""
        if self.resumo_gravado:
            return
        self.gravar('resumo', estado, bateria, t, voltas=voltas,
                    destinos_falhos=self.destinos_falhos,
                    docks_confirmados=self.docks_confirmados,
                    tentativas_dock=self.tentativas_dock,
                    bateria_minima=self.bateria_minima,
                    duracao_s=round(self._relogio_parede() - self._parede_inicio, 3),
                    codigo_saida=codigo_saida)
        self.resumo_gravado = True

    def fechar(self):
        if not self._arquivo.closed:
            self._arquivo.close()

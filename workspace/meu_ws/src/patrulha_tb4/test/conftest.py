"""Apoio dos testes L0: configuração de exemplo, mapa de mentira e um mundo simulado.

Nada aqui usa ROS. O `Mundo` faz o papel do navegador, da doca e da bateria: executa as
ações que `decidir()` devolve e devolve os resultados, em passos de 1 s.
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from patrulha_tb4 import decisao as d  # noqa: E402
from patrulha_tb4.config import montar  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line('markers', 'req(id): requisito do DEFINE.md que o teste prova')


BASE = {
    'ambiente': 'leve',
    'modelo': 'standard',
    'mapa': 'mapa.yaml',
    'pose_inicial': {'x': 0.0, 'y': 0.0, 'yaw_graus': 0},
    'aproximacao_doca': {'x': 0.5, 'y': 0.5, 'yaw_graus': 0},
    'pontos': [
        {'x': 1.0, 'y': 0.5, 'yaw_graus': 0},
        {'x': 1.0, 'y': 1.5, 'yaw_graus': 90},
        {'x': 0.5, 'y': 1.5, 'yaw_graus': 180},
    ],
}


def dados_config(**mudancas):
    """Cópia da configuração de exemplo, com seções trocadas ou removidas (valor None)."""
    dados = copy.deepcopy(BASE)
    for campo, valor in mudancas.items():
        if valor is None:
            dados.pop(campo, None)
        else:
            dados[campo] = valor
    return dados


def fazer_config(**mudancas):
    return montar(dados_config(**mudancas), '/tmp/config-de-teste.yaml', 'hash-de-teste')


@pytest.fixture
def cfg():
    return fazer_config()


def escrever_mapa(pasta, linhas, resolucao=0.5, origem=(0.0, 0.0, 0.0), nome='mapa'):
    """Grava um mapa de mentira. `linhas` é texto: '.' livre, '#' ocupada, '?' desconhecida.

    A primeira linha do texto é o topo do mapa (y maior), como numa imagem.
    """
    valores = {'.': 254, '#': 0, '?': 205}
    largura = len(linhas[0])
    pixels = bytes(valores[c] for linha in linhas for c in linha)
    (pasta / f'{nome}.pgm').write_bytes(
        f'P5\n# mapa de teste\n{largura} {len(linhas)}\n255\n'.encode() + pixels)
    (pasta / f'{nome}.yaml').write_text(
        f'image: {nome}.pgm\nmode: trinary\nresolution: {resolucao}\n'
        f'origin: [{origem[0]}, {origem[1]}, {origem[2]}]\n'
        'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n')
    return pasta / f'{nome}.yaml'


class Mundo:
    """Um robô de mentira para rodar `decidir()` em sequência, 1 s por passo."""

    def __init__(self, cfg, bateria=0.5, na_base=True, descarga=0.002, carga=0.05,
                 duracao_destino=10, duracao_aproximacao=10, duracao_base=2,
                 falhar_dock=0, dock_sem_confirmar=0, falhar_undock=False,
                 pontos_inalcancaveis=(), publica_bateria=True, parar_bateria_em=None,
                 servidores_ok=True, publica_doca=True, usa_sim_time=False, relogio_ate=None,
                 pedido_doca_em=None):
        self.cfg = cfg
        self.estado = d.Estado()
        self.t = 0.0
        self.bateria = bateria
        self.na_base = na_base
        self.descarga, self.carga = descarga, carga
        self.duracoes = {d.DESTINO: duracao_destino, d.APROXIMACAO: duracao_aproximacao,
                         d.DOCK: duracao_base, d.UNDOCK: duracao_base}
        self.falhar_dock = falhar_dock
        self.dock_sem_confirmar = dock_sem_confirmar
        self.falhar_undock = falhar_undock
        self.pontos_inalcancaveis = set(pontos_inalcancaveis)
        self.publica_bateria = publica_bateria
        self.parar_bateria_em = parar_bateria_em
        self.servidores_ok = servidores_ok
        self.publica_doca = publica_doca
        self.usa_sim_time = usa_sim_time
        self.relogio_ate = relogio_ate  # o /clock para neste instante (tempo de relógio)
        self.pedido_doca_em = pedido_doca_em  # o serviço voltar_doca é chamado neste instante
        self.sinal = False
        self.ativa = None  # (ação, argumento, instante em que termina)
        self.ultima_bateria = None
        self.t_bateria = None
        self.eventos = []      # dicionários, com 't', 'estado' e 'bateria'
        self.acoes = []        # (t, ação)
        self.codigo = None
        self.bateria_minima = bateria

    def passo(self):
        self.t += 1.0
        self.bateria = min(1.0, max(0.0, self.bateria + (self.carga if self.na_base
                                                         else -self.descarga)))
        self.bateria_minima = min(self.bateria_minima, self.bateria)
        publica = self.publica_bateria and (self.parar_bateria_em is None
                                            or self.t < self.parar_bateria_em)
        if publica:
            self.ultima_bateria, self.t_bateria = self.bateria, self.t

        resultado = None
        if self.ativa is not None and self.t >= self.ativa[2]:
            resultado = self._terminar(*self.ativa[:2])
            self.ativa = None

        # Com tempo simulado, o relógio do ROS só anda enquanto o /clock chega.
        agora, parede_relogio = self.t, None
        if self.usa_sim_time:
            ultimo_clock = self.t if self.relogio_ate is None else min(self.t, self.relogio_ate)
            if ultimo_clock <= 0:
                agora = None  # o /clock nunca chegou
            else:
                agora, parede_relogio = ultimo_clock, 1000.0 + ultimo_clock
        entrada = d.Entrada(
            parede=1000.0 + self.t, agora=agora,
            bateria=self.ultima_bateria, t_bateria=self.t_bateria,
            na_base=self.na_base if self.publica_doca else None,
            servidores_ok=self.servidores_ok, resultado=resultado, sinal=self.sinal,
            usa_sim_time=self.usa_sim_time, parede_relogio=parede_relogio,
            # Nível, como no nó: depois de chamado, o pedido não some (PAT-23e).
            pedido_doca=self.pedido_doca_em is not None and self.t >= self.pedido_doca_em)
        saida = d.decidir(self.estado, entrada, self.cfg)
        self.estado = saida.estado
        for evento in saida.eventos:
            self.eventos.append({'t': self.t, 'estado': saida.estado.fase,
                                 'bateria': self.ultima_bateria, **evento})
        for acao in saida.acoes:
            self.acoes.append((self.t, acao))
            if acao[0] == d.CANCELAR:
                self.ativa = None
            elif acao[0] == d.ENCERRAR:
                self.codigo = acao[1]
            else:
                argumento = acao[1] if len(acao) > 1 else None
                self.ativa = (acao[0], argumento, self.t + self.duracoes[acao[0]])

    def _terminar(self, acao, argumento):
        if acao == d.DESTINO:
            if argumento in self.pontos_inalcancaveis:
                return d.Resultado(d.DESTINO, d.FALHOU, 6)
            return d.Resultado(d.DESTINO, d.SUCESSO, 4)
        if acao == d.APROXIMACAO:
            return d.Resultado(d.APROXIMACAO, d.SUCESSO, 4)
        if acao == d.DOCK:
            if self.falhar_dock > 0:
                self.falhar_dock -= 1
                return d.Resultado(d.DOCK, d.FALHOU, 6)
            if self.dock_sem_confirmar > 0:
                self.dock_sem_confirmar -= 1
                return d.Resultado(d.DOCK, d.SUCESSO, 4)  # diz que encaixou, mas não encaixou
            self.na_base = True
            return d.Resultado(d.DOCK, d.SUCESSO, 4)
        if acao == d.UNDOCK:
            if self.falhar_undock:
                return d.Resultado(d.UNDOCK, d.FALHOU, 6)
            self.na_base = False
            return d.Resultado(d.UNDOCK, d.SUCESSO, 4)
        raise ValueError(acao)

    def rodar(self, passos, ate=None):
        """Roda até `passos` passos, ou até o código de saída, ou até `ate(mundo)` ser verdade."""
        for _ in range(passos):
            self.passo()
            if self.codigo is not None or (ate is not None and ate(self)):
                break
        return self

    def nomes(self):
        return [evento['evento'] for evento in self.eventos]

    def acoes_enviadas(self):
        return [acao[0] for _, acao in self.acoes]

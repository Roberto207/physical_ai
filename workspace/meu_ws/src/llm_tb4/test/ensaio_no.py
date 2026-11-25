"""Ensaio do nó num contêiner sem rede, com um Ollama falso e lento. Não toca o robô.

Rodar na raiz do repositório:
    docker run --rm --network none -e COMPILAR_WS=patrulha_tb4,llm_tb4 -e ROS_DOMAIN_ID=43 \
        -e ROS_LOCALHOST_ONLY=1 -v "$PWD/workspace:/workspace:ro" \
        -v "$PWD/workspace/mapas:/mapas:ro" physical-ai:base \
        python3 /workspace/meu_ws/src/llm_tb4/test/ensaio_no.py
O nome não começa com test_ de propósito: precisa do ROS e do pacote compilado.
"""
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import rclpy
from std_msgs.msg import Bool, String

FALSO = 'ollama_url:=http://127.0.0.1:18080/api/chat'
atraso = [2.0]
registro = []
pronto = []
falhas = []


class OllamaFalso(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        frase = corpo['messages'][1]['content']
        time.sleep(atraso[0])
        if ' x ' in frase:
            resposta = {'acao': 'ir_para_coordenadas', 'local': 'nenhum'}
        else:
            resposta = {'acao': 'ir_para', 'local': 'ponto_4'}
        saida = json.dumps({'message': {'content': json.dumps(resposta)}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(saida)

    def log_message(self, *args):
        pass


def subir(*argumentos):
    processo = subprocess.Popen(
        ['ros2', 'launch', 'llm_tb4', 'natural_language_nav_launch.py', 'namespace:=/robot1',
         *argumentos], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True)
    threading.Thread(target=lambda: [registro.append(linha.rstrip()) for linha in processo.stdout],
                     daemon=True).start()
    return processo


def encerrar(processo):
    if processo.poll() is None:
        os.killpg(processo.pid, signal.SIGINT)
        processo.wait(timeout=20)


def conferir(nome, condicao):
    print('OK    ' if condicao else 'FALHOU', nome)
    if not condicao:
        falhas.append(nome)


def achou(*partes):
    return any(all(parte in linha for parte in partes) for linha in registro)


def ros(*argumentos):
    saida = subprocess.run(['ros2', *argumentos], capture_output=True, text=True, timeout=30)
    return saida.stdout + saida.stderr


def main():
    servidor = ThreadingHTTPServer(('127.0.0.1', 18080), OllamaFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    rclpy.init()
    no = rclpy.create_node('ensaio')
    no.create_subscription(Bool, '/robot1/ready_for_input',
                           lambda m: pronto.append(m.data), 10)
    publicador = no.create_publisher(String, '/robot1/user_input', 10)

    def girar(segundos, ate=None):
        fim = time.time() + segundos
        while time.time() < fim:
            rclpy.spin_once(no, timeout_sec=0.05)
            if ate and ate():
                return True
        return False

    def enviar(texto):
        publicador.publish(String(data=texto))

    processo = subir(FALSO, 'bateria_simulada:=0.9')
    conferir('declara-se pronto depois de consultar o modelo',
             girar(30, lambda: pronto[-1:] == [True]))
    conferir('avisa o freio', achou('FREIO DE ESTACIONAMENTO'))

    atraso[0] = 0.2
    pronto.clear()
    enviar('vai pra janela')
    conferir('interpreta e registra sem executar', girar(
        10, lambda: achou('DECISAO', 'vai pra janela', 'ir_para:ponto_4', 'não executado')))
    conferir('ready vai a False e volta a True',
             girar(5, lambda: pronto[-1:] == [True]) and False in pronto)
    enviar('vá para x -0.586 y -0.807')
    conferir('coordenada livre do mapa é aceita', girar(
        10, lambda: achou('ir_para_coordenadas:-0.586,-0.807', "'x': -0.586")))
    girar(1)
    enviar('vá para x 100 y 100')
    conferir('coordenada fora do mapa é recusada', girar(
        10, lambda: achou('x 100 y 100', 'recusar', 'fora_do_mapa')))

    girar(1)
    atraso[0] = 4.0
    enviar('vai pra mesa central')
    girar(0.6)
    enviar('vai pra porta agora')
    conferir('ocupado: outro pedido é ignorado',
             girar(3, lambda: achou('OCUPADO', 'vai pra porta agora')))
    inicio = time.time()
    enviar('robô, para!')
    conferir('ocupado: "pare" é atendido na hora', girar(
        2, lambda: achou('DECISAO', 'robô, para!', 'parar')) and time.time() - inicio < 1.5)
    conferir('a interpretação em andamento é descartada',
             girar(10, lambda: achou('DESCARTADO', 'mesa central')))
    conferir('o pedido descartado não vira decisão',
             not achou('DECISAO', 'vai pra mesa central'))
    conferir('o pedido ignorado não é processado depois',
             not achou('DECISAO', 'vai pra porta agora'))
    conferir('volta a ficar pronto', girar(5, lambda: pronto[-1:] == [True]))

    topicos = ros('topic', 'list', '--no-daemon')
    conferir('tópicos oficiais no namespace',
             '/robot1/user_input' in topicos and '/robot1/ready_for_input' in topicos)
    conferir('sem comando de velocidade nem ações',
             'cmd_vel' not in topicos and '_action' not in topicos)
    resposta = ros('param', 'set', '/robot1/llm_node', 'parking_brake', 'false', '--no-daemon')
    conferir('não dá para soltar o freio em execução', 'successful' not in resposta.lower())

    atraso[0] = 30.0
    enviar('vai pra janela')
    girar(1)
    inicio = time.time()
    encerrar(processo)
    girar(1)
    conferir('Ctrl+C no meio de uma consulta encerra rápido e sem erro',
             time.time() - inicio < 8 and not achou('Traceback') and not achou('process has died'))

    atraso[0] = 0.2
    registro.clear()
    processo = subir('parking_brake:=false')
    girar(15, lambda: achou('recusado'))
    conferir('freio desligado: o nó se recusa a iniciar',
             achou('parking_brake:=false recusado') and not achou('DECISAO'))
    encerrar(processo)

    registro.clear()
    processo = subir('ollama_url:=http://127.0.0.1:1/api/chat')
    conferir('sem Ollama: avisa', girar(20, lambda: achou('não respondeu')))
    girar(2)
    enviar('pare')
    conferir('sem Ollama: "pare" ainda funciona',
             girar(5, lambda: achou('DECISAO', "'pare'", 'parar')))
    enviar('vai pra janela')
    conferir('sem Ollama: movimento é recusado',
             girar(10, lambda: achou('vai pra janela', 'recusar')))
    encerrar(processo)

    if falhas:
        print('\n'.join(registro[-40:]))
    print('FALHAS:', len(falhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())

"""Terminal de conversa com o nó: cada linha digitada é publicada em `user_input`.

Fica ligado o tempo todo, para o "pare" sair na hora (abrir um contêiner por mensagem leva
segundos). Linha vazia (só Enter) envia "pare". Fechar este terminal NÃO para o robô.

    ros2 run llm_tb4 falar --ros-args -r __ns:=/robot1
"""
import sys
import threading
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool, String

from llm_tb4.entrada import limpar

ESPERA_DESTINATARIO_S = 5.0


def main(args=None):
    rclpy.init(args=args)
    no = Node('llm_falar')
    publicador = no.create_publisher(String, 'user_input', 10)
    no.create_subscription(
        Bool, 'ready_for_input',
        lambda m: print('\n[nó pronto]' if m.data else '\n[nó ocupado]', flush=True), 10)

    executor = SingleThreadedExecutor()
    executor.add_node(no)
    sair = threading.Event()

    def girar():
        while not sair.is_set() and rclpy.ok():
            executor.spin_once(timeout_sec=0.1)

    giro = threading.Thread(target=girar, daemon=True)
    giro.start()
    print('Escreva o pedido e Enter. Só Enter envia "pare". Ctrl+D sai (não para o robô).')
    try:
        while True:
            digitado = input('> ')
            # Um caractere quebrado derrubava este terminal, e com ele o caminho do "pare".
            texto = limpar(digitado).strip() or 'pare'
            if limpar(digitado) != digitado:
                print(f'Caractere inválido ignorado. Enviando: "{texto}"', flush=True)
            limite = time.monotonic() + ESPERA_DESTINATARIO_S
            while publicador.get_subscription_count() == 0 and time.monotonic() < limite:
                time.sleep(0.05)
            if publicador.get_subscription_count() == 0:
                print('NINGUÉM RECEBEU: o nó llm não está visível.', flush=True)
                continue
            # Sem esperar confirmação de entrega: a espera segura o teclado por mais de 1 s e
            # atrasaria um "pare" digitado em seguida. A resposta aparece no log do nó.
            publicador.publish(String(data=texto))
            if texto == 'pare':
                print('"pare" enviado.', flush=True)
    except (EOFError, KeyboardInterrupt):
        print('\nSaindo.')
    finally:
        # Para a thread antes de desmontar o ROS: sair no meio de um giro aborta o processo.
        sair.set()
        giro.join(timeout=2)
        no.destroy_node()
        rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Terminal de pedidos: cada linha digitada é publicada em `user_input`; só Enter envia "pare".

Fica ligado o tempo todo para o "pare" sair na hora: um `ros2 topic pub` por mensagem leva
segundos para achar o nó pelo Discovery Server. Fechar este terminal NÃO para o robô.
Pelo PC do lab use scripts/falar.sh.
"""
import sys
import threading
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String


def limpar(linha):
    """Tira os bytes que não formam um caractere UTF-8. O Backspace num terminal sem `stty
    iutf8` apaga só um byte da letra acentuada; o Python o guarda como "surrogate" e o ROS
    se recusava a publicá-lo (UnicodeEncodeError no robô, 2026-11-25)."""
    return linha.encode('utf-8', 'surrogateescape').decode('utf-8', 'ignore')


def main():
    rclpy.init()
    no = Node('llm_falar')
    publicador = no.create_publisher(String, 'user_input', 10)
    executor = SingleThreadedExecutor()
    executor.add_node(no)
    threading.Thread(target=executor.spin, daemon=True).start()
    print('Escreva o pedido e Enter. Só Enter envia "pare". Ctrl+D sai (não para o robô).')
    try:
        while True:
            texto = limpar(input('> ')).strip() or 'pare'
            prazo = time.monotonic() + 5
            while publicador.get_subscription_count() == 0 and time.monotonic() < prazo:
                time.sleep(0.05)
            if publicador.get_subscription_count() == 0:
                print('NINGUÉM RECEBEU: o nó do LLM não está visível (scripts/llm.sh rodando?).')
                continue
            publicador.publish(String(data=texto))
            print(f'enviado: "{texto}"')
    except (EOFError, KeyboardInterrupt):
        print('\nSaindo.')
    finally:
        no.destroy_node()
        rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())

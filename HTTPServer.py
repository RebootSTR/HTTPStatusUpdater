# @rebootstr

import socket
import sys
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')


class HTTPServer:

    def __init__(self):
        self.started = False
        self.sock = None
        self.start()

    def start(self):
        if self.started:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ("", 8081)
        self.sock.bind(server_address)
        self.sock.listen(1)
        logging.info("Server started on %s:%d", server_address[0], server_address[1])

    def get(self):
        connection, client_address = self.sock.accept()
        data = connection.recv(64)
        connection.close()

        return data.decode(encoding="utf-8"), client_address

    def get_bytes(self):
        connection, client_address = self.sock.accept()
        d = connection.recv(64)
        data = b""
        while not d == b"":
            data += d
            d = connection.recv(64)
        connection.close()
        return data, client_address

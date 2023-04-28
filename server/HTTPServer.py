# @rebootstr

import socket
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class HTTPServer:

    def __init__(self):
        self.sock = None
        self.start()

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ("", 8081)
        self.sock.bind(server_address)
        self.sock.listen(1)
        logging.info("Server started on %s:%d", server_address[0], server_address[1])

    def get_bytes(self):
        connection, client_address = self.sock.accept()
        connection: socket.socket
        connection.settimeout(5)
        d = connection.recv(64)
        data = b""
        while not d == b"":
            data += d
            d = connection.recv(64)
        connection.close()
        return data, client_address

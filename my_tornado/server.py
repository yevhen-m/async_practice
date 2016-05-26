import socket
import selectors

from classes import *  # noqa
from stream import *  # noqa


class TCPServer:

    def __init__(self):
        self.ioloop = IOLoop()

        self.server_sock = socket.socket()
        self.server_sock.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_REUSEADDR, 1)

    def bind(self, port):
        self.server_sock.bind(('', port))

    def listen(self, backlog=10):
        self.server_sock.listen(backlog)

    def start(self):
        self.ioloop.add_handler(self.server_sock,
                                selectors.EVENT_READ,
                                self.accept)
        self.ioloop.start()

    def accept(self):
        client, addr = self.server_sock.accept()
        print('Connection from', *client.getpeername())
        handle_client(Stream(client))


@coroutine
def handle_client(client_stream):
    while True:
        data = yield client_stream.recv()
        if not data.strip():
            break
        yield client_stream.send(data.upper())
    print('Handled', *client_stream.getpeername())
    client_stream.close()


if __name__ == "__main__":
    PORT = 8000

    server = TCPServer()
    server.bind(PORT)
    server.listen()
    server.start()

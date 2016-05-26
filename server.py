import socket
import selectors

from classes import *  # noqa


class TCPServer:

    def __init__(self):
        self.ioloop = IOLoop()

        self.server_sock = socket.socket()
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
        client.send(b'hello\n')
        client.close()


@coroutine
def handle_client(client):
    data = yield client.recv()
    yield client.send(data.upper())
    print('Handled', *client.getpeername())


if __name__ == "__main__":
    PORT = 8000

    server = TCPServer()
    server.bind(PORT)
    server.listen()
    server.start()

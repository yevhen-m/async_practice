import socket
import selectors

from ioloop import IOLoop
from stream import Stream
from gen import coroutine, sleep


class TCPServer:

    def __init__(self):
        self.ioloop = IOLoop()
        self.port = None

        self.server_sock = socket.socket()
        self.server_sock.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_REUSEADDR, 1)

    def bind(self, port):
        self.port = port
        self.server_sock.bind(('', port))

    def listen(self, backlog=10):
        self.server_sock.listen(backlog)

    def start(self):
        self.ioloop.add_handler(self.server_sock,
                                selectors.EVENT_READ,
                                self.accept)
        print('Server running on port', self.port)
        self.ioloop.start()

    def accept(self):
        client, addr = self.server_sock.accept()
        stream = Stream(client)
        print(stream, 'incoming connection')
        handle_client(stream)


@coroutine
def handle_client(client_stream):
    while True:
        data = yield client_stream.recv()
        if not data.strip():
            break
        print(client_stream, 'sleeping')
        yield from sleep(5)
        print(client_stream, 'resuming')
        yield client_stream.send(data.upper())
    print(client_stream, 'connection closed')
    client_stream.close()


if __name__ == "__main__":
    import sys

    try:
        script_name, port = sys.argv
    except ValueError:
        port = 8000

    server = TCPServer()
    server.bind(port)
    server.listen()
    server.start()

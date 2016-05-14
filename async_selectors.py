import socket
import contextlib
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ
import collections


@contextlib.contextmanager
def close_socket(socket):
    try:
        yield
    finally:
        socket.close()


class MyClientSocket:

    def __init__(self, sock):
        self.sock = sock
        self.sock.setblocking(0)
        self.request = None

    def __getattr__(self, attr):
        return getattr(self.sock, attr)


class TCPServer:

    def __init__(self, port):
        self.port = port
        self.sock = None
        self.selector = DefaultSelector()
        self.buffers = collections.defaultdict(list)

    def run(self):
        server_sock = self._create_socket()

        with close_socket(server_sock):
            try:
                client_sock, remote_addr = self.sock.accept()
            except BlockingIOError:
                pass
            self.selector.register(self.sock, EVENT_READ)

            while True:
                ready = self.selector.select()
                for key, events in ready:
                    if key.fileobj is self.sock:
                        self._accept_client()
                        continue

                    client_sock = key.fileobj
                    if events == EVENT_READ:
                        self._read_request(client_sock)
                        if not client_sock.request:
                            continue
                        self._handle_received_request(client_sock)

                    elif events == EVENT_WRITE:
                        self._write_response(client_sock)

    def _handle_received_request(self, client_sock):
        self.responses[client_sock] = client_sock.request.upper()
        self.selector.unregister(client_sock)
        self.selector.register(client_sock, EVENT_WRITE)

    def _write_response(self, client_sock):
        response = self.responses[client_sock].encode('utf8')
        client_sock.sendall(response)
        self.selector.unregister(client_sock)
        client_sock.close()

    def _create_socket(self):
        self.sock = socket.socket()
        self.sock.bind(('', self.port))
        self.sock.setblocking(False)
        self.sock.listen(10)
        self.responses = {}
        return self.sock

    def _accept_client(self):
        sock, remote_addr = self.sock.accept()
        client_sock = MyClientSocket(sock)
        print('Client connected from', *remote_addr)
        # Make client socket nonblocking
        self.selector.register(client_sock, EVENT_READ)

    def _get_client_name(self, client_sock):
        return '{} {}'.format(*client_sock.getpeername())

    def _read_request(self, client_sock):
        client_name = self._get_client_name(client_sock)
        print('Reading from client', client_name)

        while True:
            try:
                chunk = client_sock.recv(1024)
            except BlockingIOError:
                return
            print('Received chunk from client', client_name)
            if chunk.endswith(b'end'):
                print('All data received from client', client_name)
                request = b''.join(self.buffers[client_sock]).decode('utf8')
                client_sock.request = request
            else:
                self.buffers[client_sock].append(chunk)


if __name__ == "__main__":
    PORT = 8000

    TCPServer(PORT).run()

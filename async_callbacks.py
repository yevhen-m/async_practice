import socket

from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector


class TCPServer:

    def __init__(self, port):
        self.port = port
        self.sock = None
        self.selector = DefaultSelector()

    def run(self):
        '''
        Start running TCPServer on its port.
        '''
        server_sock = self._create_socket()

        with server_sock:
            try:
                client_sock, remote_addr = self.sock.accept()
            except BlockingIOError:
                pass
            # Register callback to run, when server socket is read-ready
            self.selector.register(self.sock, EVENT_READ,
                                   lambda: self._accept_client())

            while True:
                ready = self.selector.select()
                for key, events in ready:
                    # Each socket has a callback attached to it
                    # Server socket has a callback to accept connection
                    # Client socket has a callback to read/write data
                    callback = key.data
                    callback()

    def _write_response(self, client_sock, response):
        client_name = self._get_client_name(client_sock)
        while True:
            if not response:
                # All response sent
                print('Response sent to client', client_name)
                self.selector.unregister(client_sock)
                client_sock.close()
                break
            try:
                bytes_sent = client_sock.send(response)
                print(bytes_sent, 'bytes sent to client', client_name)
                response = response[bytes_sent:]
            except BlockingIOError:
                print('Socket blockes for', client_name)
                self.selector.unregister(client_sock)
                self.selector.register(
                    client_sock, EVENT_WRITE,
                    lambda: self._write_response(client_sock, response)
                )
                break

    def _create_socket(self):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        self.sock.setblocking(False)
        self.sock.listen(10)
        self.responses = {}
        return self.sock

    def _accept_client(self):
        client_sock, remote_addr = self.sock.accept()
        client_sock.setblocking(False)
        print('Client connected from', *remote_addr)
        # Make client socket nonblocking
        self.selector.register(client_sock, EVENT_READ,
                               lambda: self._read_request(client_sock))

    def _get_client_name(self, client_sock):
        return '{} {}'.format(*client_sock.getpeername())

    def _read_request(self, client_sock, buffer=None):
        if buffer is None:
            buffer = []

        client_name = self._get_client_name(client_sock)

        while True:
            try:
                chunk = client_sock.recv(1024)
                buffer.append(chunk)
            except BlockingIOError:
                self.selector.unregister(client_sock)
                self.selector.register(
                    client_sock, EVENT_READ,
                    lambda: self._read_request(client_sock, buffer)
                )
                break

            print('Received chunk from client', client_name)
            if chunk.endswith(b'end'):
                buffer.append(chunk)
                print('Got all data from client', client_name)
                request = b''.join(buffer).decode('utf8')
                response = (request.upper() * 100).encode('utf8')
                self.selector.unregister(client_sock)
                self.selector.register(
                    client_sock, EVENT_WRITE,
                    lambda: self._write_response(client_sock, response)
                )
                break


if __name__ == "__main__":
    PORT = 8000

    TCPServer(PORT).run()

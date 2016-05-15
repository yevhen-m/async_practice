import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ
import collections


class TCPServer:

    def __init__(self, port):
        self.port = port
        self.sock = None
        self.selector = DefaultSelector()
        self.buffers = collections.defaultdict(list)

    def run(self):
        '''
        Start running TCPServer on its port.
        '''
        server_sock = self._create_socket()

        with server_sock:
            try:
                client_sock, remote_addr = self.sock.accept()
                client_sock.setblocking(False)
            except BlockingIOError:
                pass
            self.selector.register(self.sock, EVENT_READ)

            while True:
                ready = self.selector.select()
                for key, events in ready:
                    if key.fileobj is self.sock:
                        # This is my server socket, so I accept incoming
                        # connection
                        self._accept_client()
                        continue

                    client_sock = key.fileobj
                    if events == EVENT_READ:
                        # Read data from client socket
                        self._read_request(client_sock)
                    elif events == EVENT_WRITE:
                        # Now I can send response to the client
                        self._write_response(client_sock)

    def _write_response(self, client_sock):
        '''
        We can write data to client socket, so I get its response and
        write it. I check how much bytes were sent and shorten response
        accordingly. If all data is sent, I unregister socket and close it.
        '''
        client_name = self._get_client_name(client_sock)
        while True:
            response = self.responses[client_sock]
            if not response:
                # All response sent
                break
            try:
                bytes_sent = client_sock.send(response)
            except BlockingIOError:
                return

            print(bytes_sent, 'bytes sent to client', client_name)
            self.responses[client_sock] = response[bytes_sent:]

        print('Response sent to client', client_name)
        self.selector.unregister(client_sock)
        client_sock.close()

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
        self.selector.register(client_sock, EVENT_READ)

    def _get_client_name(self, client_sock):
        return '{} {}'.format(*client_sock.getpeername())

    def _read_request(self, client_sock):
        '''
        I read client request in chunks and accumulate them in
        self.buffers. When all data received, I set client_sock request
        attribute value to the joined buffer data.
        '''
        client_name = self._get_client_name(client_sock)

        while True:
            try:
                chunk = client_sock.recv(1024)
            except BlockingIOError:
                return
            print('Received chunk from client', client_name)
            if chunk.endswith(b'end'):
                self.buffers[client_sock].append(chunk)
                print('Got all data from client', client_name)
                request = b''.join(self.buffers[client_sock]).decode('utf8')
                response = (request.upper() * 100).encode('utf8')
                self.responses[client_sock] = response
                self.selector.unregister(client_sock)
                self.selector.register(client_sock, EVENT_WRITE)
            else:
                self.buffers[client_sock].append(chunk)


if __name__ == "__main__":
    PORT = 8000

    TCPServer(PORT).run()

import socket

from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector


class Future:

    def __init__(self):
        self.callback = None

    def resolve(self):
        self.callback()


class Task:
    '''
    This class has to drive its generator, receive futures from it
    and attach callbacks to them.
    '''

    def __init__(self, gen):
        self.gen = gen
        self.step()

    def step(self):
        try:
            # Socket for this future has already been registered in
            # selector. We need it here to attach a callback.
            fut = next(self.gen)
        except StopIteration:
            return
        fut.callback = self.step


class TCPServer:

    def __init__(self, port):
        self.port = port
        self.sock = None
        self.selector = DefaultSelector()

        # Advance self.listen() method. A future has been attached to the
        # server socket, that has been registered in selector. And a callback
        # has been attached to this future.
        Task(self.listen())

    def run(self):
        while True:
            ready = self.selector.select()
            for key, events in ready:
                fut = key.data
                fut.resolve()

    def listen(self):
        server_sock = self._create_socket()
        with server_sock:
            try:
                client_sock, remote_addr = self.sock.accept()
            except BlockingIOError:
                pass

            fut = Future()
            self.selector.register(self.sock, EVENT_READ, fut)
            while True:
                yield fut
                Task(self.handle_client())

    def handle_client(self):
        client_sock, remote_addr = self.sock.accept()
        client_sock.setblocking(False)
        client_name = '{} {}'.format(*client_sock.getpeername())
        print('Connected', client_name)

        # Register client socket for reading and wait for this event
        fut = Future()
        self.selector.register(client_sock, EVENT_READ, fut)
        yield fut

        buffer = []
        while True:
            try:
                chunk = client_sock.recv(1024)
                buffer.append(chunk)
            except BlockingIOError:
                # Yield the same future, so we don't need to register
                # it again. By the way, callback is the same for all
                # futures, so it doesn't matter in my case.
                yield fut
                continue

            print('Received chunk from client', client_name)
            if chunk.endswith(b'end'):
                print('Got all data from client', client_name)
                request = b''.join(buffer).decode('utf8')
                response = (request.upper() * 100).encode('utf8')
                self.selector.unregister(client_sock)
                fut = Future()
                self.selector.register(client_sock, EVENT_WRITE, fut)
                break

        # This future was attached to the client_sock
        yield fut
        while True:
            try:
                bytes_sent = client_sock.send(response)
                print(bytes_sent, 'bytes sent to client', client_name)
                response = response[bytes_sent:]
            except BlockingIOError:
                print('Socket blockes for', client_name)
                yield fut
                continue
            else:
                if not response:
                    # All response sent
                    print('Response sent to client', client_name)
                    self.selector.unregister(client_sock)
                    client_sock.close()
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


if __name__ == "__main__":
    PORT = 8000

    TCPServer(PORT).run()

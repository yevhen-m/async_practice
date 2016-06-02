import socket

from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector


class TCPServer:

    def __init__(self, port=8000):
        self.port = port
        self._create_socket(port)
        self.selector = DefaultSelector()
        self.responses = {}

    def _create_socket(self, port):
        self.sock = socket.socket()
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(10)

    def run(self):
        with self.sock:
            # Register server_sock for READ events and attach event
            # callback to it; callback will be executed, when this socket
            # pops from the selector
            self.selector.register(self.sock, EVENT_READ,
                                   lambda: self._accept_client())
            # And now we start to listen for incoming connections
            while True:
                ready = self.selector.select()
                for key, events in ready:
                    # Each socket has a callback attached to it
                    # Server socket has a callback to accept connection
                    # Client socket has a callback to read/write data
                    callback = key.data
                    callback()

    def _accept_client(self):
        sock, addr = self.sock.accept()
        client = Client(sock)
        print(client, 'incoming connection')
        self.selector.register(client, EVENT_READ,
                               lambda: self._read_request(client))

    def _read_request(self, client):
        # Now we want to receive 2kB from the client
        chunk = client.recv(1024).strip()
        if chunk:  # non-empty chunk
            print(client, chunk)
            client.inbuffer.append(chunk)
            # This client is still registered for READ events in the
            # selector
            return
        # We received empty chunk, so it is all the incoming data
        # from this client
        print(client, 'request received')
        client.outbuffer = b''.join(client.inbuffer).upper() + b'\n'
        # Now we unregister this socket for READ events and register it
        # for WRITE events
        self.selector.unregister(client)
        self.selector.register(client, EVENT_WRITE,
                               lambda: self._write_response(client))

    def _write_response(self, client):
        if client.outbuffer:
            bytes_sent = client.send(client.outbuffer)
            client.outbuffer = client.outbuffer[bytes_sent:]
            # This client is still registered in selector for WRITE events
            return

        print(client, 'handled')
        self.selector.unregister(client)
        client.close()


class Client:

    def __init__(self, sock):
        self.sock = sock
        self.inbuffer = []
        self.outbuffer = None

    def __getattr__(self, attrname):
        return getattr(self.sock, attrname)

    def __repr__(self):
        return '%s %s' % self.getpeername()


if __name__ == "__main__":
    TCPServer().run()

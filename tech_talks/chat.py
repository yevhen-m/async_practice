import socket

from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector


class Chat:

    def __init__(self):
        self.client_id = 0
        self.clients = {}

    def register_client(self, client):
        self.client_id += 1
        cid = self.client_id
        client.id = cid
        # Add this client to self.clients table
        self.clients[cid] = client

    def generate_greeting(self, client):
        other_clients = self.clients.keys() - {client.id}
        greeting = 'Hello, your chat ID is %s\n' % client.id
        if other_clients:
            greeting += ('Other clients IDs: %s\n' %
                         ', '.join(map(str, set(self.clients) - {client.id})))
        else:
            greeting += 'No other clients yet\n'
        return greeting.encode('utf8')

    MSG_SEPARATOR = ': '

    def route_message(self, client, message):
        # Decode recieved message, generate new message for clients and
        # encode it back.
        str_msg = message.decode('utf8')
        msg_parts = str_msg.partition(self.MSG_SEPARATOR)
        cid, text = int(msg_parts[0]), msg_parts[2]

        new_msg = str(client.id) + self.MSG_SEPARATOR + text + '\n'
        if cid:
            # This is a monocast message
            try:
                receivers = [self.clients[cid]]
            except KeyError:
                # Echo message to the client
                receivers = [self.clients[client.id]]
        else:
            # This is a broadcast message
            receivers = set(self.clients.values()) - {client}
        return receivers, new_msg.encode('utf8')


class TCPServer:

    def __init__(self, port=8000):
        self.port = port
        self._create_socket(port)
        self.selector = DefaultSelector()
        self.responses = {}
        self.chat = Chat()

    def _create_socket(self, port):
        self.sock = socket.socket()
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
        # Arrange to write greeting to the client
        self.chat.register_client(client)
        self.selector.register(client, EVENT_WRITE,
                               lambda: self._write_greeting(client))

    def _write_greeting(self, client):
        greeting = self.chat.generate_greeting(client)
        client.send(greeting)
        self.selector.unregister(client)
        # Wait message from the client
        self.selector.register(client, EVENT_READ,
                               lambda: self._read_request(client))

    def _read_request(self, client):
        received_msg = client.recv(1024).strip()

        # Chat exiting does not work yet :-)
        if not received_msg:
            client.close()
            print(client, 'connection closed')
            return
        # -------------------------------

        # Get receivers for this message
        receivers, new_msg = self.chat.route_message(client, received_msg)
        for rec in receivers:
            # There is a tricky thing here: late binding in closures
            self.selector.unregister(rec)
            callback = (lambda client=rec, new_msg=new_msg:
                        self._write_response(client, new_msg))
            self.selector.register(rec, EVENT_WRITE, callback)

    def _write_response(self, client, new_msg):
        client.send(new_msg)
        # Now wait for messages from the client again
        self.selector.unregister(client)
        self.selector.register(client, EVENT_READ,
                               lambda: self._read_request(client))


class Client:

    def __init__(self, sock):
        self.id = None
        self.sock = sock
        self.inbuffer = []
        self.outbuffer = None

    def __getattr__(self, attrname):
        return getattr(self.sock, attrname)

    def __repr__(self):
        return '%s %s' % self.getpeername()


if __name__ == "__main__":
    TCPServer().run()

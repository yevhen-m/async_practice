import socket
import functools
import selectors


class Future:

    def __init__(self):
        self.result = None
        self.callback = None

    def add_done_callback(self, cb):
        self.callback = cb

    def set_result(self, result):
        self.result = result
        self.callback(self)


class Runner:

    def __init__(self, gen, result_future):
        self.gen = gen
        self.result_future = result_future  # future returned by async func
        self.received_future = None  # future received from gen
        self.ioloop = IOLoop.current()

    def run(self):
        try:
            self.received_future = self.gen.send(None)
        except StopIteration as e:
            self.result_future.set_result(e.value)
            return
        self.ioloop.add_future(self.received_future,
                               lambda f: self.run())


class IOLoop:

    _current = None

    def __init__(self):
        self.handlers = {}
        self.callbacks = []
        self.running = False
        self.selector = selectors.DefaultSelector()

    @classmethod
    def current(cls):
        '''
        We have only one IOLoop instance.
        '''
        if not cls._current:
            cls._current = cls()
        return cls._current

    def add_handler(self, sock, event, handler):
        assert event in (selectors.EVENT_READ, selectors.EVENT_WRITE)

        self.handlers[sock] = handler
        self.selector.register(sock, event)

    def remove_handler(self, sock):
        self.handlers.pop(sock, None)
        self.selector.unregister(sock)

    def stop(self):
        self.running = False

    def add_future(self, future, callback):
        future.add_done_callback(lambda f: self.add_callback(callback,
                                                             future))

    def add_callback(self, callback, *args, **kwargs):
        self.callbacks.append(functools.partial(callback, *args, **kwargs))

    def start(self):
        self.running = True
        while True:
            # new callbacks will be executed on the next iteration
            callbacks = self.callbacks
            self.callbacks = []
            for cb in callbacks:
                cb()

            poll_timeout = 0.0 if self.callbacks else None

            # We can exit loop if `stop()` method was called during
            # during callback execution
            if not self.running:
                break

            events = self.selector.select(poll_timeout)
            for key, mask in events:
                sock = key.fileobj
                # Call the handler for this socket
                self.handlers[sock]()


class TCPServer:

    def __init__(self):
        self.ioloop = IOLoop.current()

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


if __name__ == "__main__":
    PORT = 8000

    server = TCPServer()
    server.bind(PORT)
    server.listen()
    server.start()

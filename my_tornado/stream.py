from classes import *  # noqa


class Stream:

    def __init__(self, sock):
        self.sock = sock
        self.ioloop = IOLoop()

    def __getattr__(self, attrname):
        return getattr(self.sock, attrname)

    def __repr__(self):
        return '%s %s' % self.sock.getpeername()

    def recv(self):
        future = Future()

        def handler():
            future.set_result(self.sock.recv(65536))
            self.ioloop.remove_handler(self.sock)

        self.ioloop.add_handler(self.sock, selectors.EVENT_READ, handler)
        return future

    def send(self, data):
        future = Future()

        def handler():
            self.sock.send(data)
            future.set_result(None)
            self.ioloop.remove_handler(self.sock)

        self.ioloop.add_handler(self.sock, selectors.EVENT_WRITE, handler)
        return future

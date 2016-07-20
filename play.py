import types
import collections
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE


# I have two coroutines, that are used for communication with the loop.
# These are used to wait for the socket to become readable or
# writeable.
@types.coroutine
def read_wait(sock):
    yield 'read_wait', sock

# I need this decorator to be able to use await keyword with these
# coroutines


@types.coroutine
def write_wait(sock):
    yield 'write_wait', sock


class Loop:

    def __init__(self):
        self.ready = collections.deque()
        self.selector = DefaultSelector()

    async def sock_accept(self, sock):
        '''
        Wait for the server socket to become readable, accept a new
        client and return her socket, addr pair.
        '''
        await read_wait(sock)
        return sock.accept()

    async def sock_recv(self, sock, maxbytes):
        '''
        Wait for the socket to become readable, read data from the
        socket and return data.
        '''
        await read_wait(sock)
        return sock.recv(maxbytes)

    async def sock_sendall(self, sock, data):
        '''
        While we have some data to send, wait for the socket to become
        writeable and send some data.
        '''
        while data:
            await write_wait(sock)
            nbytes = sock.send(data)
            # Modify data according to the number of bytes sent this time
            data = data[nbytes:]

    def create_task(self, coro):
        self.ready.append(coro)

    def run_forever(self):
        while True:
            while not self.ready:
                events = self.selector.select()
                for key, _ in events:
                    self.selector.unregister(key.fileobj)
                    self.ready.append(key.data)

            while self.ready:
                # I need this task in another method, so I attach it here
                self.current_task = self.ready.popleft()
                try:
                    # drive the coroutine to the next yield
                    op, *args = self.current_task.send(None)
                except StopIteration:
                    pass
                else:
                    # call method on myself
                    # this methods will register sockets with selector
                    getattr(self, op)(*args)

    def read_wait(self, sock):
        # When this socket is ready, drive this task to the next yield
        self.selector.register(sock, EVENT_READ, self.current_task)

    def write_wait(self, sock):
        self.selector.register(sock, EVENT_WRITE, self.current_task)

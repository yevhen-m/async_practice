import functools
import heapq
import selectors
import time


def singleton(cls):
    instance = []

    def inner():
        if not instance:
            instance.append(cls())
        return instance[0]

    return inner


@singleton
class IOLoop:

    def __init__(self):
        self.handlers = {}
        self.callbacks = []
        self.timeouts = []
        self.running = False
        self.selector = selectors.DefaultSelector()

    def time(self):
        return time.time()

    def add_timeout(self, timeout):
        heapq.heappush(self.timeouts, timeout)

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
        future.add_done_callback(lambda f:
                                 self.add_callback(callback, future))

    def add_callback(self, callback, *args, **kwargs):
        self.callbacks.append(functools.partial(callback, *args, **kwargs))

    def start(self):
        self.running = True
        while True:
            # We can exit loop if `stop()` method was called during
            # during callback execution
            if not self.running:
                break

            timeout = None

            # Calculate poll timeout

            if self.callbacks:
                timeout = 0
            elif self.timeouts:
                when = self.timeouts[0].time
                deadline = max(0, when - self.time())
                if timeout is None:
                    timeout = deadline
                else:
                    timeout = min(timeout, deadline)

            # Poll

            events = self.selector.select(timeout)
            for key, mask in events:
                sock = key.fileobj
                self.callbacks.append(self.handlers[sock])

            now = self.time()
            while self.timeouts:
                timeout = self.timeouts[0]
                if now < timeout.time:
                    break
                timeout = heapq.heappop(self.timeouts)
                self.add_callback(timeout.callback)

            # Run callbacks

            callbacks = self.callbacks
            self.callbacks = []
            for cb in callbacks:
                cb()

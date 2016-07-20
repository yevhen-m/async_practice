import heapq
import time
import functools
import selectors
import collections


Timeout = collections.namedtuple('Timeout', 'time callback')


def sleep(seconds):
    future = Future()
    loop = IOLoop()
    time_ = loop.time() + seconds
    loop.add_timeout(Timeout(time_, lambda: future.set_result(None)))
    return future


def coroutine(fn):

    def inner(*args, **kwargs):
        result_future = Future()
        Runner(fn(*args, **kwargs), result_future)
        return result_future

    return inner


def singleton(cls):
    instance = []

    def inner():
        if not instance:
            instance.append(cls())
        return instance[0]

    return inner


class Future:

    def __init__(self):
        self.result = None
        self.callbacks = []

    def add_done_callback(self, cb):
        self.callbacks.append(cb)

    def set_result(self, result):
        self.result = result
        for cb in self.callbacks:
            cb(self)


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

            now = self.time()
            while self.timeouts:
                timeout = heapq.heappop(self.timeouts)
                if now < timeout.time:
                    heapq.heappush(self.timeouts, timeout)
                    break
                self.callbacks.append(timeout.callback)

            # Can't figure out how to get poll_timeout neatly
            events = self.selector.select(0.0)
            for key, mask in events:
                sock = key.fileobj
                # Call the handler for this socket
                self.callbacks.append(self.handlers[sock])

            # new callbacks will be executed on the next iteration
            callbacks = self.callbacks
            self.callbacks = []
            for cb in callbacks:
                cb()


class Runner:

    def __init__(self, gen, result_future):
        self.gen = gen
        # future returned by the async function
        self.result_future = result_future
        self.ioloop = IOLoop()
        self.next = None
        # And now we start to drive the generator
        self.run()

    def run(self):
        try:
            future = self.gen.send(self.next)
        except StopIteration as e:
            self.result_future.set_result(e.value)
            return

        def callback(f):
            self.next = f.result
            self.run()

        self.ioloop.add_future(future, callback)

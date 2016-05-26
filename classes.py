import functools
import selectors


def coroutine(fn):

    def inner(*args, **kwargs):
        result_future = Future()
        Runner(fn(*args, **kwargs), result_future)
        return result_future

    return inner


def singleton(cls):
    instance = None

    def inner():
        nonlocal instance
        if instance is None:
            instance = cls()
        return instance

    return inner


@singleton
class IOLoop:

    def __init__(self):
        self.handlers = {}
        self.callbacks = []
        self.running = False
        self.selector = selectors.DefaultSelector()

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


class Runner:

    def __init__(self, gen, result_future):
        self.gen = gen
        # future returned by the async function
        self.result_future = result_future
        # future received from the generator
        self.received_future = None
        self.ioloop = IOLoop()
        # And now we start to drive the generator
        self.run()

    def run(self):
        try:
            self.received_future = self.gen.send(None)
        except StopIteration as e:
            self.result_future.set_result(e.value)
            return
        self.ioloop.add_future(self.received_future,
                               lambda f: self.run())


class Future:

    def __init__(self):
        self.result = None
        self.callback = None

    def add_done_callback(self, cb):
        self.callback = cb

    def set_result(self, result):
        self.result = result
        self.callback(self)



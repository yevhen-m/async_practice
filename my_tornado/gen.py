import collections
from ioloop import IOLoop


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

    def __iter__(self):
        yield self
        return self.result

    __await__ = __iter__


def coroutine(fn):

    def inner(*args, **kwargs):
        result_future = Future()
        Runner(fn(*args, **kwargs), result_future)
        return result_future

    return inner


Timeout = collections.namedtuple('Timeout', 'time callback')


@coroutine
def sleep(seconds):
    future = Future()
    loop = IOLoop()
    time_ = loop.time() + seconds
    loop.add_timeout(Timeout(time_, lambda: future.set_result(None)))
    yield from future


async def sleep_await(seconds):
    future = Future()
    loop = IOLoop()
    time_ = loop.time() + seconds
    loop.add_timeout(Timeout(time_, lambda: future.set_result(None)))
    await future


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

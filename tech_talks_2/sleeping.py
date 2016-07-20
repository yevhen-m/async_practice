import datetime
import heapq
import types
import time


class Task:
    """Represent how long a coroutine should wait before starting again.

    Comparison operators are implemented for use by heapq. Two-item
    tuples unfortunately don't work because when the datetime.datetime
    instances are equal, comparison falls to the coroutine and they don't
    implement comparison methods, triggering an exception.
    """

    def __init__(self, wait_until, coro):
        self._value = None
        self.coro = coro
        self.waiting_until = wait_until

    def __eq__(self, other):
        return self.waiting_until == other.waiting_until

    def __lt__(self, other):
        return self.waiting_until < other.waiting_until


class SleepingLoop:
    """An event loop focused on delaying execution of coroutines."""

    def __init__(self, *coros):
        self._new = coros
        self._waiting = []

    def run_until_complete(self):
        for coro in self._new:
            # Start a coroutine
            wait_for = coro.send(None)
            # Wrap a coroutine in a Task and put it into the heap
            heapq.heappush(self._waiting, Task(wait_for, coro))

        # Keep running until there is no more work to do.
        while self._waiting:
            now = datetime.datetime.now()

            # Get the coroutine with the soonest resumption time.
            task = heapq.heappop(self._waiting)

            if now < task.waiting_until:
                # We're ahead of schedule; wait until it's time to resume.
                delta = task.waiting_until - now
                # We can block here!
                time.sleep(delta.total_seconds())
                now = datetime.datetime.now()

            try:
                # It's time to resume the coroutine.
                wait_until = task.coro.send(now)
                heapq.heappush(self._waiting, Task(wait_until, task.coro))
            except StopIteration:
                # The coroutine is done, don't put it into the heap now
                pass


@types.coroutine
def sleep(seconds):
    """Pause a coroutine for the specified number of seconds."""
    now = datetime.datetime.now()
    wait_until = now + datetime.timedelta(seconds=seconds)
    # wait_until is a datetime object
    # actual gets now datetime object from the loop
    actual = yield wait_until
    return actual - now


async def countdown(label, counter, *, delay=0):
    """Countdown a launch for `counter` seconds, waiting `delay` seconds.
    """
    print(label, 'waiting', delay, 'seconds before starting countdown')
    delta = await sleep(delay)
    print(label, 'starting after waiting')

    while counter:
        print(label, counter)
        waited = await sleep(1)
        counter -= 1

    print(label, 'finished')


def main():
    """Start the event loop, counting down 3 separate launches."""
    loop = SleepingLoop(countdown('A', 5),
                        countdown('B', 3, delay=2),
                        countdown('C', 4, delay=1))

    start = datetime.datetime.now()
    loop.run_until_complete()

    print('Total elapsed time is',
          (datetime.datetime.now() - start).total_seconds())


if __name__ == '__main__':
    main()

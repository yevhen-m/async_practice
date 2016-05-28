import socket
import select
import time


def countdown(n=10**8):
    while n > 0:
        n -= 1
        yield n


def send_data(data, port=8000):
    sock = socket.socket()
    sock.connect(('localhost', port))
    sock.setblocking(0)

    data = data * 10 * 1024 * 1024
    print('Bytes to send', len(data))

    total_sent = 0
    while len(data):
        try:
            sent = sock.send(data)
            total_sent += sent
            data = data[sent:]
        except BlockingIOError:
            yield sock
    print('Bytes sent', total_sent)


if __name__ == "__main__":
    tasks = [countdown(),
             send_data(data=b'foobar', port=8000),
             send_data(data=b'barfoo', port=8001)]  # these are generators objects

    write_waiting = {}  # {sock: task} mapping

    start = time.time()
    while tasks or write_waiting:
        new_tasks = []
        for task in tasks:
            try:
                response = next(task)
                if isinstance(response, int):  # this is countdown task
                    new_tasks.append(task)
                else:
                    write_waiting[response] = task  # this was a socket
            except StopIteration:
                pass

        if write_waiting:
            # We need to set timeout to 0, because our countdown task is
            # waiting in the to be executed
            readable, writeable, errors = select.select([], write_waiting, [], 0)
            for sock in writeable:
                new_tasks.append(write_waiting.pop(sock))

        tasks = new_tasks

    print('%.1f' % (time.time() - start), 'sec')

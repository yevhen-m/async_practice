import select
import socket
import time

from nonblocking_example_2 import countdown


def send_data(data=b'foobar', port=8000):
    sock = socket.socket()
    # It will never wait for the operation to complete; it will put as much
    # data in the buffer as possible and return. If the buffer is full and
    # we continue to send data, exception is raised.
    sock.setblocking(0)
    try:
        # Start establishing connection
        sock.connect(('localhost', port))
    except BlockingIOError:
        pass

    data = data * 10 * 1024 * 1024  # 60MB

    while len(data):
        try:
            bytes_sent = sock.send(data)
            data = data[bytes_sent:]
        except BlockingIOError:
            # print('Blocked (resend_dataing %s)' % len(data))

            # Buffer is full, so we need to wait some time (blocked in select)
            # Select helps us to deal with multiple file descriptors at once
            # We just block until our socket becomes writeable again
            select.select([], [sock], [])


if __name__ == "__main__":
    start = time.time()
    send_data(port=8000)
    # send_data(port=8001)
    for _ in countdown(): pass
    print('%.1f' % (time.time() - start), 'sec')

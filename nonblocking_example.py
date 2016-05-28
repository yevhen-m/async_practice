import select
import socket
import time

sock = socket.socket()
# It will never wait for the operation to complete; it will put as much
# data in the buffer as possible and return. If the buffer is full and
# we continue to send data, exception is raised.
sock.setblocking(0)
try:
    # Start establishing connection
    sock.connect(('localhost', 8000))
except BlockingIOError:
    pass

data = b'foobar' * 10 * 1024 * 1024  # 60MB

start = time.time()

while len(data):
    try:
        bytes_sent = sock.send(data)
        data = data[bytes_sent:]
    except BlockingIOError:
        print('Blocked (remaining %s)' % len(data))

        # Buffer is full, so we need to wait some time (blocked in select)
        # Select helps us to deal with multiple file descriptors at once
        # We just block until our socket becomes writeable again
        select.select([], [sock], [])


from nonblocking_example_2 import countdown
for _ in countdown(): pass

print('%.1f' % (time.time() - start), 'sec')

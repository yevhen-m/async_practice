import socket

sock = socket.socket()
sock.connect(('localhost', 8000))

data = b'foobar' * 10 * 1024 * 1024  # 60MB
# 1. Write buffer will get fill up
# 2. The kernel will put the process to sleep until the data in the buffer
# is transferred to destination and the buffer is empty again
# 3. The kernel will wake the process up again to get the next chunk of data
# that is to be transferred
assert sock.send(data) == len(data)
# Here is some other code, that will be executed only after all the
# data will be sent
print('Now next code is executed...')

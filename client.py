# client.py

import socket
import time

PORT = 8000


def client():
    # Client sends chunks of data every half a second.
    sock = socket.socket()
    # Decrease recv buffer size for this socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)  # 2304
    sock.connect(('localhost', PORT))

    num_of_chunks = 10
    for i in range(1, num_of_chunks):
        sock.send(b'hello')
        print('Sent chunk', i)
        time.sleep(.5)

    sock.send(b'end')

    buf = []
    while True:
        # Accumulate received chunks in a buffer
        # and join them when server closes the connection
        chunk = sock.recv(1024)
        if chunk:
            print('Received chunk from', *sock.getpeername())
            buf.append(chunk)
            time.sleep(.5)
        else:
            # server closed its connection
            response = b''.join(buf).decode('utf8')
            print('Response with len', len(response), 'received')
            print(response[:15] + '...')
            return


if __name__ == "__main__":
    client()

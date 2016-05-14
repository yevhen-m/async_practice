# client.py

import socket
import time

PORT = 8000


def client():
    # Client sends chunks of data every half a second.
    sock = socket.socket()
    sock.connect(('localhost', PORT))

    for i in range(1, 21):
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
            buf.append(chunk)
        else:
            # server closed its connection
            response = b''.join(buf).decode('utf8')
            print('Response with len', len(response), 'received')
            print(response[:15] + '...')
            return


if __name__ == "__main__":
    client()

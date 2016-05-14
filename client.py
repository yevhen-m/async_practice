# client.py

import socket


def client(message):
    sock = socket.socket()
    sock.connect(('localhost', 8000))
    sock.send(message.encode('utf8'))

    buf = []
    while 1:
        # Accumulate received chunks in a buffer
        # and join them when server closes the connection
        chunk = sock.recv(1024)
        if chunk:
            buf.append(chunk)
        else:
            # server closed its connection
            response = b''.join(buf).decode('utf8')
            print(response)
            return


if __name__ == "__main__":
    client('hello')

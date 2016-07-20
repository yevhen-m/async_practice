import socket


PORT = 8000


qa = (('What is your name?', 'My name is Sir Lancelot of Camelot.'),
      ('What is your quest?', 'To seek the Holy Grail.'),
      ('What is your favorite color?', 'Blue.'))
qadict = dict(qa)


def recv_until(sock, suffix):
    message = b''
    suffix_bytestr = suffix.encode('utf8')
    while not message.endswith(suffix_bytestr):
        data = sock.recv(4096)
        if not data:
            raise EOFError('socket closed before we saw {}'.format(suffix))
        message += data
    return message.decode('utf8')


def setup():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    sock.listen(5)
    return sock


def handle_client(client_sock):
    try:
        message = recv_until(client_sock, '?')
        answer = qadict[message]
        client_sock.sendall(answer.encode('utf8'))
    except EOFError:
        client_sock.close()


def server_loop(listen_sock):
    while True:
        client_sock, addr = listen_sock.accept()
        handle_client(client_sock)


if __name__ == "__main__":
    listen_sock = setup()
    server_loop(listen_sock)

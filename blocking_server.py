'''
This simple tcp server prints to stdout incoming connections, received
messages and closed connections. When server receives whitespace string
it terminates the connection.
'''
import socket
import sys


# Port as a second cli argument is optional
port = int(sys.argv[-1]) if len(sys.argv) > 1 else 8000


server_sock = socket.socket()
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('', port))
server_sock.listen(5)

with server_sock:
    while True:
        client, addr = server_sock.accept()
        client_name = '%s %s' % client.getpeername()
        print(client_name, 'incoming connection')

        while True:
            data = client.recv(1024).strip()
            if not data:
                break
            print(client_name, data)

        print(client_name, 'connection closed')
        client.close()

import socket
import select


# Create a non-blocking server socket
server_sock = socket.socket()
server_sock.bind(('', 8000))
server_sock.setblocking(0)
server_sock.listen(10)


rlist = {server_sock}  # waiting for READ events
wlist = {}  # waiting for WRITE events
xlist = []  # waiting for ERROR events


while 1:
    (ready_to_read,
     ready_to_write,
     errors) = select.select(rlist, wlist, xlist, timeout=0.5)

    for sock in ready_to_read:
        if sock is server_sock:
            # Accept a new client
            client_sock, remote_addr = sock.accept()
            rlist.add(client_sock)
        else:
            # This is one of the client sockets
            request = sock.recv(1024)
            print('{0[0]} : {1}'.format(sock.getpeername(), request))
            # We have received data and now we want to write
            rlist.remove(sock)
            response = request.upper()
            wlist[sock] = response

    for sock in ready_to_write:
        sock.send(wlist[sock])
        sock.close()
        # Client has been handled so remove the socket
        del wlist[sock]

'''
Accept incoming connections, ready request string from the client and
respond with this string uppercased.
'''
import socket
import select


# Create a server socket
server_sock = socket.socket()
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('', 8000))
server_sock.listen(10)


rlist = {server_sock}  # waiting for READ events
wlist = {}  # waiting for WRITE events
xlist = []  # waiting for ERROR events


with server_sock:
    while True:
        (ready_to_read,
         ready_to_write,
         errors) = select.select(rlist, wlist, xlist, 0.5)

        for sock in ready_to_read:
            if sock is server_sock:
                # Accept a new client
                client_sock, remote_addr = sock.accept()
                print(*client_sock.getpeername(), 'incoming connection')
                rlist.add(client_sock)
            else:
                # This is one of the client sockets
                request = sock.recv(1024)
                # We have received data and now we want to send response
                # to the client; remove this socket from those waiting for
                # READ events, and add it to those, waiting for WRITE events
                rlist.remove(sock)
                response = request.upper()
                wlist[sock] = response

        # Some of our clients are ready to receive their responses
        # Write uppercase request message and close the connection
        for sock in ready_to_write:
            sock.send(wlist[sock])
            print(*sock.getpeername(), 'handled')
            sock.close()
            del wlist[sock]

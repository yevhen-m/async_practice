import types


# I have two coroutines, that are used for communication with the loop.
# These are used to wait for the socket to become readable or
# writeable.
@types.coroutine
def read_wait(sock):
    yield 'read_wait', sock

# I need this decorator to be able to use await keyword with these
# coroutines
@types.coroutine
def write_wait(sock):
    yield 'write_wait', sock

# class Loop:
#   ready -- a queue of ready to run coroutines

#   My Loop has async methods:
#   sock_accept(sock)
#       wait for the socket to become readable
#       accept a new client and create a new task for her
#   sock_recv(sock, maxbytes)
#       wait for the sock to become readable
#       read data from the socket and return it
#   sock_sendall(client, data)
#       while we have some data to send
#       wait for the socket to become writeable
#       send bytes to the socket
#       modify data according to the number of bytes sent
#   create_task(coro)
#       append given coroutine to the queue of ready to run coroutines
#   run_forever()
#       while we have some coroutines to run
#       get a coroutine
#       and drive it to the next yield
#   read_wait(sock)
#       register this socket for read_event in the selector
#   write_wait(sock)
#       register this socket for write_event in the selector

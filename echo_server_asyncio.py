import socket
import asyncio


loop = asyncio.get_event_loop()

async def echo_server(address):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = await loop.sock_accept(sock)
        print('Connection from', addr)
        loop.create_task(echo_handler(client))

async def echo_handler(client):
    with client:
        while True:
            data = await loop.sock_recv(client, 1024)
            if not data:
                # Client closed the connection, we received ''
                break
            await loop.sock_sendall(client, b'Got: ' + data)
    print('Connection closed')

if __name__ == "__main__":
    loop.create_task(echo_server(('', 8000)))
    loop.run_forever()

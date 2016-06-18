import time
import socket


def benchmark(addr, nmessages):
    sock = socket.socket()
    sock.connect(addr)
    start = time.time()
    for _ in range(nmessages):
        sock.send(b'x\n')
        sock.recv(1024)
    end = time.time()
    print('{:.0f} messages/sec'.format(nmessages / (end - start)))

if __name__ == "__main__":
    benchmark(('localhost', 8000), 10**5)

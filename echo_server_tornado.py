import tornado.gen
import tornado.tcpserver
import tornado.iostream
import tornado.ioloop


class MyTCPServer(tornado.tcpserver.TCPServer):

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        print('Connection from', address)
        while True:
            try:
                data = yield stream.read_until(b'\n')
            except tornado.iostream.StreamClosedError:
                # client closed the connection
                break
            yield stream.write(b'Got: ' + data)
        stream.close()
        print('Connection closed')


if __name__ == "__main__":
    srv = MyTCPServer()
    srv.listen(8000)
    tornado.ioloop.IOLoop.current().start()

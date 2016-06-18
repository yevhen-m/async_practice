import tornado.gen
import tornado.tcpserver
import tornado.ioloop


class MyTCPServer(tornado.tcpserver.TCPServer):

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        print('Connection from', address)
        msg = yield stream.read_until(b'\n')
        yield stream.write(b'Got: ' + msg)
        stream.close()


if __name__ == "__main__":
    srv = MyTCPServer()
    srv.listen(8000)
    tornado.ioloop.IOLoop.current().start()

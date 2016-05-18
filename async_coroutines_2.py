import select
import socket

import queue


class Task:
    tid = 0

    def __init__(self, gen):
        Task.tid += 1
        self.tid = Task.tid
        self.gen = gen
        self.send_value = None

    def step(self):
        return self.gen.send(self.send_value)

    def __repr__(self):
        return self.gen.gi_code.co_name


class SysCall:
    pass


class NewTask(SysCall):

    def __init__(self, gen):
        self.gen = gen

    def handle(self):
        tid = self.sched.new(self.gen)
        self.task.send_value = tid
        self.sched.schedule(self.task)


class ReadWait(SysCall):

    def __init__(self, fd):
        self.fd = fd

    def handle(self):
        self.sched.wait_for_read(self.task, self.fd)


class WriteWait(SysCall):

    def __init__(self, fd):
        self.fd = fd

    def handle(self):
        self.sched.wait_for_write(self.task, self.fd)


class Scheduler:

    def __init__(self):
        self.ready = queue.Queue()
        self.tasks = {}
        self.read_waiting = {}
        self.write_waitign = {}

    def wait_for_read(self, task, fd):
        self.read_waiting[fd] = task

    def wait_for_write(self, task, fd):
        self.write_waitign[fd] = task

    def iopoll(self, timeout):
        if self.read_waiting or self.write_waitign:
            r, w, e = select.select(self.read_waiting,
                                    self.write_waitign,
                                    [], timeout)
            for fd in r:
                task = self.read_waiting.pop(fd)
                self.schedule(task)

            for fd in w:
                task = self.write_waitign.pop(fd)
                self.schedule(task)

    def iotask(self):
        while True:
            if self.ready.empty():
                self.iopoll(None)
            else:
                self.iopoll(0)
            yield

    def new(self, gen):
        task = Task(gen)
        self.tasks[task.tid] = task
        self.schedule(task)
        return task.tid

    def schedule(self, task):
        print(task, 'was scheduled')
        self.ready.put(task)

    def exit(self, task):
        del self.tasks[task.tid]
        print('Task', task.tid, 'terminated')

    def mainloop(self):
        # Create a new iotask and push it into the queue
        self.new(self.iotask())
        while self.tasks:
            task = self.ready.get()
            print(task)
            try:
                result = task.step()
                if isinstance(result, SysCall):
                    result.task = task
                    result.sched = self
                    result.handle()
                    continue
            except StopIteration:
                self.exit(task)
                continue
            self.schedule(task)


def handle_client(sock, address):
    print('Client connected', address)
    while True:
        yield ReadWait(sock)
        data = sock.recv(65536)
        print('Received data', data)
        if not data.strip():
            break
        yield WriteWait(sock)
        sock.send(data)
    sock.close()
    print('Client handled')
    yield


def server(port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(10)
    while True:
        yield ReadWait(sock)
        client, addr = sock.accept()
        yield NewTask(gen=handle_client(client, addr))


if __name__ == "__main__":
    sch = Scheduler()
    # Create a new server task and push it into the ready queue
    sch.new(server(8000))
    sch.mainloop()

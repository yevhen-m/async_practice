# A subroutine
def add(x, y):
    yield x + y


def main():
    r = yield add(2, 2)
    print(r)
    yield


def run():
    m = main()
    sub = main.send(None)
    result = sub.send(None)
    m.send(result)

Introduction
------------
PEP 0492 Coroutines with async and await syntax

* native coroutines declaration
    * async def functions event if they do not contain await, are always coroutines
    * it's a `SyntaxError` to have yield or yield from in an async function
    * async functions return a coroutine object (like generator functions return generator objects)
    * `await` is used to obtain result from a coroutine
    * `await` uses `yield from` but it also validates its argument (it must be an awaitable object)
    - native coroutine object
    - coroutine decorated generator-based object
    - object with `__await__` method returning an iterator

* `async for` -- `__aiter__` and `__anext__`
* `async with` -- `__aenter__` and `__aexit__`
    * we can do async io in this methods

* Any `yield from` chain of calls ends with a yield, every await is suspended by a yield somewhere
  down the chain of await calls.


``` python
>>> async def read_data(db):
...     pass
...
>>>
>>> # StopIteration is not propagated out of coroutine and is replaced with RuntimeError
>>> async def raiser():
...     raise StopIteration
...
>>> r = raiser()
>>> # we can drive a coroutine calling its send method with None
>>> # (or throw and exception into it)
>>> r.send(None)
RuntimeError: coroutine raised StopIteration

>>> r = raiser()
>>> del r
RuntimeWarning: coroutine 'r' was never awaited

>>> async def coro():
...     return 'spam'
...
>>> try:
...     c = coro()
...     c.send(None)
... except StopIteration as err:
...     # return value if in the `value` attribute
...     print('Got:', err.value)
...
Got: spam

>>> async def coro_age():
...     return 88
...
>>> async def coro_name(name, coro):
...     # obtaining result from coro
...     age = await coro
...     return name, age
...
>>> try:
...     c = coro_name('John', coro_age())
...     c.send(None)
... except StopIteration as err:
...     print('Got:',  *err.value)
...
Got: John 88

>>> # interoperability between existing generator-based coroutines and native coroutines
>>> from types import coroutine
>>> @coroutine
... def driver(coro):
...     name, age = yield from coro
...     print('Got:', name, age)
...
>>> d = driver(coro_name('Pete', coro_age()))
>>> d.send(None)
Got: Pete 88

>>>
```

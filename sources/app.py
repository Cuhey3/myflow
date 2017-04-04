import asyncio
from producer import Producer, Route
from endpoints import Endpoints
from exchange import Exchange


def foo(string):
    def process(exchange):
        assert (isinstance(exchange.get_body(), str))
        exchange.set_body(exchange.get_body() + ' ' + string)
        return exchange

    return process


def ppp(exchange):
    print(exchange.get_body())


def body(exchange):
    return exchange.get_body()


def predicate(exchange):
    return True

(Route('myroute').to(foo('bar')).to(foo('wao')).when([
        (predicate, Producer(foo('poko')).to(foo('pai'))),
        (False, Producer(foo('pen')).to(foo('pee')).when([
            (False, Producer(foo('nyao'))),
            (False, Producer(foo('passo')))]))
        ])
    .to(foo('final'))
    .filter(True)
    .to(foo('papaiya'))
    .split(body, Producer(ppp))
) #yapf:disable

exchange = Endpoints().send_to('myroute', Exchange("foo"))

if exchange:
    print(exchange.get_body())

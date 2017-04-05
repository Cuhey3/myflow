import asyncio
from producer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from expression import *


def foo(string):
    async def process(exchange):
        assert (isinstance(exchange.get_body(), str))
        exchange.set_body(exchange.get_body() + ' ' + string)
        return exchange

    return process


async def ppp(exchange):
    print(exchange.get_body())


def predicate(exchange):
    return True

(RouteId('myroute').to(foo('bar')).to(foo('wao')).when([
        (predicate, To(foo('poko')).to(foo('pai'))),
        (False, To(foo('pen')).to(foo('pee')).when([
            (False, To(foo('nyao'))),
            (False, To(foo('passo')))]))
        ])
    .to(foo('final'))
    .to(log({}))
    .filter(True)
    .to(foo('papaiya'))
    #.split(body, To(ppp))
) #yapf:disable

RouteId('myfoo').to(cache({
    'to': 'myroute',
    'keys': [header('pon.puu')]
})).to(direct({
    'to': 'myroute'
})).split(body(), To(ppp))


async def tasks_main():
    #yapf:disable
    exchange = await Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
    exchange = await Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
    #yapf:enable
    if exchange:
        print(exchange.get_body())


asyncio.get_event_loop().run_until_complete(tasks_main())
'''
#yapf:disable
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
#yapf:enable
if exchange:
    print(exchange.get_body())
'''

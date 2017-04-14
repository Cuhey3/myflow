import asyncio
from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *


def foo(string):
    async def processor(exchange):
        assert (isinstance(exchange.get_body(), str))
        exchange.set_body(exchange.get_body() + ' ' + string)
        return exchange

    return processor


async def ppp(exchange):
    print(exchange.get_body())


def predicate(exchange):
    return True



(RouteId('myroute').process(lambda exchange: exchange.set_body('bar'))
        .to(foo('wao'))
        .to(set_header('ch','boo'))
        .when([
        (exists(header('ch')), To(foo('poko')).to(foo('pai'))),
        (True, To(foo('pen')).to(foo('pee')).when([
            (True, To(foo('nyao'))),
            (False, To(foo('passo')))]))
        ])
    .to(foo('final'))
    .to(log())
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


def gather_func(exchanges):
    gathered_body = exchanges[0].get_body() + " " + exchanges[1].get_body()
    exchanges[0].set_body(gathered_body)
    return exchanges[0]


RouteId('gather_a').to(foo('bon'))
(RouteId('gathering')
    .gather(
        [To(direct({'to': 'gather_a'})), To(foo('poyo')).to(foo('pin'))],
        gather_func)
    .split(body(), Process(lambda x: print(x.body)).process(lambda x:print(x.body,x.body)))
) #yapf: disable

#expect: log exchange:body {"foo": null}
(Timer({'repeatCount': 3})
    .to(set_header('foo', {'foo': None}))
    .to(to_json(header('foo')))
    .to(log())) #yapf: disable


async def tasks_main():
    #yapf:disable
    exchange = await Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
    exchange = await Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
    gathering_exchange = await Endpoints().send_to('gathering', Exchange('boo'))
    #yapf:enable
    if exchange:
        print(exchange.get_body())
    if gathering_exchange:
        #expect: boo bon boo poyo
        print('gathered:', gathering_exchange.get_body())

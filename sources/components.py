from endpoints import Endpoints


def direct(params={}):
    endpoint_to = params.get('to')

    async def processor(exchange):
        exchange = await Endpoints().send_to(endpoint_to, exchange)
        return exchange

    return processor


def log(params={}):
    async def processor(exchange):
        if params.get('body', True):
            print('log', 'exchange:body', exchange.get_body())
        if params.get('header', False):
            print('log', 'exchange:headers', exchange.get_headers())
        return exchange

    return processor


from cachetools import cached, hashkey, TTLCache
cache_object = TTLCache(maxsize=1000, ttl=60)


def cache(params):
    to = params.get('to')
    keys_expression = params.get('keys')
    assert isinstance(keys_expression, list), 'keys parameter must be list.'

    async def process(exchange):
        from util import expression_to_value
        cache_key = hashkey(
            tuple(expression_to_value(keys_expression, exchange)))
        if cache_key in cache_object:
            exchange.set_body(cache_object.get(cache_key))
            print('cache loaded', cache_key)
        else:
            exchange = await Endpoints().send_to(to, exchange)
            cache_object[cache_key] = exchange.get_body()
            print('cache saved', cache_key)
        return exchange

    return process

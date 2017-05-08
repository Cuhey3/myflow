from endpoints import Endpoints
from evaluator import evaluate_expression, body, header


def direct(params):
    assert isinstance(params, str), 'string is required as argument.'

    async def processor(exchange):
        return await Endpoints().send_to(params, exchange)

    return processor


def log(params={}):
    log_name = 'log:' + params.get('name') if 'name' in params else 'log'
    show_body = params.get('body', True)
    show_header = params.get('header', False)

    async def processor(exchange):
        if show_body:
            print(log_name, 'exchange:body', exchange.get_body())
        if show_header:
            print(log_name, 'exchange:header', exchange.get_headers())

    return processor


from cachetools import cached, hashkey


def cache(params):
    to = params.get('to')
    keys_expression = params.get('keys')
    cache_object = params.get('cache_object')
    assert isinstance(keys_expression, list), 'keys parameter must be list.'

    async def processor(exchange):
        cache_key = hashkey(
            tuple(evaluate_expression(keys_expression, exchange)))
        if cache_key in cache_object:
            exchange.set_body(cache_object.get(cache_key))
            print('cache loaded', cache_key)
        else:
            exchange = await to.get_consumer().produce(exchange)
            cache_object[cache_key] = exchange.get_body()
            print('cache saved', cache_key)
        return exchange

    return processor


def aiohttp_request(params={}):
    url_expression = params.get('url') or body()
    response_type = params.get('response_type', 'text')
    isValid = params.get('isValid', False)

    async def processor(exchange):
        url = evaluate_expression(url_expression, exchange)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if isValid:
                    exchange.set_header('validate', resp.status == 200)
                else:
                    if response_type == 'text':
                        exchange.set_body(await resp.text())
                    elif response_type == 'data':
                        exchange.set_body(await resp.read())
                    exchange.set_header('request_url', url)  #buggy
            return exchange

    return processor


def soup(func):
    async def processor(exchange):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(exchange.get_body(), 'lxml')
        exchange.set_body(func(soup))
        return exchange

    return processor


def zipper(params):
    mode = params.get('mode', 'write')
    from zipfile import ZipFile
    import zipfile
    if mode == 'open':
        expression = params.get('zip_file_name') or header('zip_file_name')

        async def processor(exchange):
            zip_file_name = evaluate_expression(expression, exchange)
            exchange.set_header('zip_file_name', zip_file_name)
            exchange.set_header('zipfile',
                                ZipFile(zip_file_name, 'w',
                                        zipfile.ZIP_DEFLATED))
            return exchange
    elif mode == 'write':
        expression = params.get('file_name')

        async def processor(exchange):
            file_name = evaluate_expression(expression, exchange)
            (exchange.get_header('zipfile') or
             exchange.parent().get_header('zipfile')).writestr(
                 file_name, exchange.get_body())
            return exchange

    elif mode == 'close':

        async def processor(exchange):
            zipFile = exchange.get_header('zipfile')
            zipFile.close()
            return exchange

    return processor

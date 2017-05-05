from endpoints import Endpoints
from evaluator import evaluate_expression


def direct(params=None):
    if params:
        if isinstance(params, dict):
            endpoint_to = params.get('to')
        elif isinstance(params, str):
            endpoint_to = params

    async def processor(exchange):
        exchange = await Endpoints().send_to(endpoint_to, exchange)
        return exchange

    return processor


def log(params={}):
    async def processor(exchange):
        log_name = 'log:' + params.get('name', '')
        if params.get('body', True):
            print(log_name, 'exchange:body', exchange.get_body())
        if params.get('header', False):
            print(log_name, 'exchange:headers', exchange.get_headers())
        return exchange

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
    url_expression = params.get('url', None)
    response_type = params.get('response_type', 'text')
    isValid = params.get('isValid', False)

    async def processor(exchange):
        if url_expression is None:
            url = exchange.get_body()
        else:
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


def soup(func, attr=None):
    async def processor(exchange):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(exchange.get_body(), 'lxml')
        elements = func(soup)
        if attr is None:
            exchange.set_body(elements)
        else:
            exchange.set_body([element.get(attr) for element in elements])
        return exchange

    return processor


def zipper(params):
    mode = params.get('mode', 'write')
    from zipfile import ZipFile
    import zipfile
    if mode == 'open':

        async def processor(exchange):
            if 'zip_file_name' in params:
                zip_file_name = evaluate_expression(
                    params.get('zip_file_name'), exchange)
                exchange.set_header('zip_file_name', zip_file_name)
            else:
                zip_file_name = exchange.get_header('zip_file_name')
            exchange.set_header('zipfile',
                                ZipFile(zip_file_name, 'w',
                                        zipfile.ZIP_DEFLATED))
            return exchange
    elif mode == 'write':

        async def processor(exchange):
            file_name = evaluate_expression(params.get('file_name'), exchange)
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

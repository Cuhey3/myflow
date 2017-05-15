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
        return exchange

    return processor


from cachetools import cached, hashkey


def cache(params):
    method = params.get('method') or 'get'
    keys_expression = params.get('keys')
    cache_object = params.get('cache_object')
    assert isinstance(keys_expression, list), 'keys parameter must be list.'

    if method == 'set':

        async def processor(exchange):
            cache_key = hashkey(
                tuple(evaluate_expression(keys_expression, exchange)))
            cache_object[cache_key] = exchange.get_body()
            return exchange

        return processor

    elif method == 'get':

        async def processor(exchange):
            cache_key = hashkey(
                tuple(evaluate_expression(keys_expression, exchange)))
            if cache_key in cache_object:
                exchange.set_body(cache_object.get(cache_key))
            else:
                to = params.get('to')
                if to:
                    exchange = await to.get_consumer().produce(exchange)
                    cache_object[cache_key] = exchange.get_body()
            return exchange

        return processor


def redis_cache(params):
    # TBD: to = params.get('to')
    method = params.get('method') or 'get'
    keys_expression = params.get('keys')
    conn_setting = params.get('conn')
    conn = None
    assert isinstance(keys_expression, list), 'keys parameter must be list.'
    import aioredis
    import json
    if method == 'set':

        async def processor(exchange):
            nonlocal conn
            if conn is None or conn.closed:
                conn = await aioredis.create_connection(**conn_setting)
                print('redis connected')
            cache_key = str(evaluate_expression(keys_expression, exchange))
            await conn.execute('set', cache_key,
                               json.dumps(exchange.get_body()))
            return exchange

        return processor

    elif method == 'get':

        async def processor(exchange):
            nonlocal conn
            if conn is None or conn.closed:
                conn = await aioredis.create_connection(**conn_setting)
                print('redis connected')
            cache_key = str(evaluate_expression(keys_expression, exchange))
            exchange.set_body(json.loads(await conn.execute('get', cache_key)))
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


def composer(composer_id, source_name):
    import copy, asyncio
    from consumer import Composer
    composer = Composer()

    async def processor(exchange):
        asyncio.get_event_loop().create_task(
            composer.send_to(composer_id, source_name, copy.deepcopy(
                exchange)))
        return exchange

    return processor


def file(params):
    mode = params.get('mode') or 'read'
    file_name_expression = params.get('file_name') or body()

    #TBD: other mode
    #TBD: file cache
    async def processor(exchange):
        if mode == 'read':
            file_name = evaluate_expression(file_name_expression, exchange)
            f = open(file_name, 'r')
            exchange.set_body(f.read())
            f.close()
        return exchange

    return processor


def markdown(params=None):
    import markdown as markdown_module
    expression = body()
    if params is not None and params.get('expression'):
        expression = params.get('expression')

    async def processor(exchange):
        value = evaluate_expression(expression, exchange)
        exchange.set_body(markdown_module.markdown(value))
        return exchange

    return processor


def jinja2_(params):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    template = Environment(loader=FileSystemLoader(
        '../public/static/templates',
        encoding='utf8')).get_template(params.get('template'))
    data_expression = params.get('data')

    async def processor(exchange):
        data = evaluate_expression(data_expression, exchange)
        exchange.set_body(template.render(data))
        exchange.set_header('content-type', 'text/html')
        return exchange

    return processor

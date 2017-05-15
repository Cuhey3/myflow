import asyncio
import os
from urllib.parse import urlparse
from consumer import Aiohttp, Any, To, RouteId
from components import cache, direct, log, redis_cache, jinja2_
from evaluator import set_body, body, header, exists, isEqualTo
from cachetools import LRUCache
antenna_cache = LRUCache(maxsize=1000)

redis_url = urlparse(os.environ['REDIS_URL'])
redis_setting = {
    'address': (redis_url.hostname, redis_url.port),
    'password': redis_url.password,
    'loop': asyncio.get_event_loop()
}

cache_get_processor = redis_cache({
    'keys': ['foo'],
    'conn': redis_setting
}) #yapf: disable

cache_set_processor = redis_cache({
    'method': 'set',
    'keys': ['foo'],
    'conn': redis_setting
}) #yapf: disable


async def update_id(exchange):
    items = exchange.get_body()
    max_ = max([item.get('id', 0) for item in items]) + 1
    for item in items:
        if 'id' not in item:
            item['id'] = max_
            max_ = max_ + 1
    return exchange


async def update_time(exchange):
    from datetime import datetime
    import pytz
    id_ = exchange.get_header('id')
    for item in exchange.get_body():
        if str(item['id']) == id_:
            item['past'] = datetime.now(
                pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")
    return exchange

(Aiohttp('/antenna')
    .to(cache_get_processor)
    .when([
        (exists(header('method')), To(direct('antenna_crud'))),
        (True, Any())])
    .to(jinja2_({
        'template': 'antenna.html',
        'data':{'items': body()}
    }))
) #yapf: disable

(RouteId('antenna_crud')
    .when([
        (isEqualTo(header('method'), 'create'), To(direct('antenna_create'))),
        (isEqualTo(header('method'), 'update'), To(direct('antenna_update'))),
        (isEqualTo(header('method'), 'delete'), To(direct('antenna_delete'))),
    ])) #yapf: disable

(RouteId('antenna_update')
    .process(lambda ex:
        [item for item in ex.get_body()
            if str(item['id']) != ex.get_header('id')]
            + [item for item in ex.get_body()
                if str(item['id']) == ex.get_header('id')])
    .to(update_time)
    .to(cache_set_processor)
) #yapf: disable

(RouteId('antenna_delete')
    .process(lambda ex:
        [item for item in ex.get_body()
            if str(item['id']) != ex.get_header('id')])
    .to(cache_set_processor)
) #yapf: disable

(RouteId('antenna_create')
    .process(lambda ex:
        ex.set_body(
            [{'name': ex.get_header('name'), 'url': ex.get_header('url', '')}]
            + ex.get_body()))
    .to(update_id)
    .to(cache_set_processor)
) #yapf: disable

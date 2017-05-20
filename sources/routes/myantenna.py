import asyncio
import os
from urllib.parse import urlparse
from consumer import Aiohttp, Any, To, RouteId, Client
from components import cache, direct, log, redis_cache, jinja2_, redirect
from evaluator import set_body, body, header, exists, isEqualTo
from cachetools import LRUCache
from settings.antenna_settings import span_option
from utility.jinja2_util import create_util
from utility.datetime_util import calc_date_from_span
from datetime import datetime
import pytz
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


def get_now(exchange):
    return datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")


def sort_func(exchange):
    items = exchange.get_body()
    now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d")
    #yapf: disable
    group1 = [item for item in items if item.get('next') == now]
    group2 = [item for item in items if item.get('next') != '' and item.get('next') < now]
    group3 = [item for item in items if item.get('next') == '' and item.get('span') != 'complete']
    group4 = [item for item in items if item.get('next') > now]
    group5 = [item for item in items if item.get('span') == 'complete']
    group1 = sorted(group1, key=lambda item: item.get('span', '') + item.get('past', ''))
    group2 = sorted(group2, key=lambda item: item.get('next', '') + item.get('span', '') + item.get('past', ''))
    group3 = sorted(group3, key=lambda item: item.get('past', ''))
    group4 = sorted(group4, key=lambda item: item.get('next', '') + item.get('span', '') + item.get('past', ''))
    group5 = sorted(group5, key=lambda item: item.get('past',''))
    #yapf: enable
    return group1 + group2 + group3 + group4 + group5


async def update_time(exchange):
    if exchange.get_header('reserve', '') != 'true' and exchange.get_header(
            'current', '') != 'true' and not exchange.get_header(
                'time_no_update', False):
        id_ = exchange.get_header('id')
        for item in exchange.get_body():
            if str(item['id']) == id_:
                item['past'] = datetime.now(
                    pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")
    return exchange

(Aiohttp('/antenna')
    .to(cache_get_processor)
    .when([
        (exists(header('method')),
            To(direct('antenna_crud')).to(redirect('/antenna'))),
        (True,
            To(jinja2_({
                'template': 'antenna.html',
                'data':{
                    'items': body(),
                    'span_list': span_option,
                    'now': get_now
                    },
                'util': create_util()
            })))])
) #yapf: disable

(RouteId('antenna_crud')
    .when([
        (isEqualTo(header('method'), 'create'), To(direct('antenna_create'))),
        (isEqualTo(header('method'), 'update'), To(direct('antenna_update'))),
        (isEqualTo(header('method'), 'delete'), To(direct('antenna_delete'))),
    ])
    .process(sort_func)
    .to(cache_set_processor)
)#yapf: disable


def item_update_by_exchange(item, exchange):
    headers = exchange.get_headers()
    span_changed_flag = True
    if 'span' in headers and 'name' in headers and 'url' in headers and 'memo' in headers:
        exchange_span = exchange.get_header('span')
        if exchange_span != 'complete':
            exchange.set_header('time_no_update', True)
        if item['span'] == exchange_span:
            span_changed_flag = False
        item['span'] = exchange_span
        item['name'] = exchange.get_header('name')
        item['url'] = exchange.get_header('url')
        item['memo'] = exchange.get_header('memo')
    if exchange.get_header('finish', 'false') == 'true':
        exchange.set_header('time_no_update', False)
        item['span'] = 'complete'
        item['next'] = ''
    elif span_changed_flag:
        current = exchange.get_header('current', 'false')
        calc_date_from_span(item, current == 'true')
    return item

(RouteId('antenna_update')
    .process(lambda ex:
        [item for item in ex.get_body()
            if str(item['id']) != ex.get_header('id')]
            + [item_update_by_exchange(item, ex) for item in ex.get_body()
                if str(item['id']) == ex.get_header('id')])
    .to(update_time)
) #yapf: disable

(RouteId('antenna_delete')
    .process(lambda ex:
        [item for item in ex.get_body()
            if str(item['id']) != ex.get_header('id')])
) #yapf: disable

(RouteId('antenna_create')
    .process(lambda ex:
        ex.set_body(
            [calc_date_from_span({'name': ex.get_header('name'), 'url': ex.get_header('url', ''), 'memo': ex.get_header('memo', ''), 'span': ex.get_header('span', '')}, ex.get_header('url', '') == '')]
            + ex.get_body()))
    .to(update_id)
) #yapf: disable


(Client('/antenna-exchange')
    .to(cache_get_processor)
    .to(direct('antenna_crud'))
    .process(lambda ex: ex.set_body('success'))
) #yapf: disable
try:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='public/static')
except:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='../public/static')
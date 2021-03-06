import asyncio
import os
from urllib.parse import urlparse
from consumer import Aiohttp, Any, To, RouteId, Context
from components import cache, direct, log, redis_cache, jinja2_, redirect
from evaluator import set_body, body, header, exists, isEqualTo
from cachetools import LRUCache
from settings.antenna_settings import span_option, span_sort_score
from utility.jinja2_util import create_util
from utility.datetime_util import calc_date_from_span, now_str, get_now
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

def sort_func(exchange):
    items = exchange.get_body()
    now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d")
    #yapf: disable
    group1 = [item for item in items if item.get('next') == now]
    group2 = [item for item in items if item.get('next') != '' and item.get('next') < now]
    group3 = [item for item in items if item.get('next') == '' and item.get('span') != 'complete']
    group4 = [item for item in items if item.get('next') > now]
    group5 = [item for item in items if item.get('span') == 'complete']
    group1 = sorted(group1, key=lambda item: span_sort_score.get(item.get('span', '')) + item.get('past', ''))
    group2 = sorted(group2, key=lambda item: item.get('next', '') + span_sort_score.get(item.get('span', '')) + item.get('past', ''))
    group3 = sorted(group3, key=lambda item: item.get('past', ''))
    group4 = sorted(group4, key=lambda item: item.get('next', '') + span_sort_score.get(item.get('span', '')) + item.get('past', ''))
    group5 = sorted(group5, key=lambda item: item.get('past',''))
    #yapf: enable
    return group1 + group2 + group3 + group4 + group5


async def simple_update_item(exchange):
    id_ = int(exchange.get_header('id'))
    now = now_str("%Y/%m/%d")
    for item in exchange.get_body():
        if item['id'] == id_:
            exchange_span = exchange.get_header('span')
            if item['span'] != exchange_span:
                item['span'] = exchange_span
                calc_date_from_span(item, item['next'] <= now)
            item['name'] = exchange.get_header('name')
            item['url'] = exchange.get_header('url')
            item['memo'] = exchange.get_header('memo')
            item['decide'] = exchange.get_header('decide')
    return exchange


def simple_update_next(prev=False):
    async def func(exchange):
        id_ = int(exchange.get_header('id'))
        for item in exchange.get_body():
            if item['id'] == id_:
                calc_date_from_span(item, prev)
        return exchange

    return func


async def simple_update_time(exchange):
    id_ = int(exchange.get_header('id'))
    for item in exchange.get_body():
        if item['id'] == id_:
            item['past'] = datetime.now(
                pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")
    return exchange


async def complete_item(exchange):
    id_ = int(exchange.get_header('id'))
    for item in exchange.get_body():
        if item['id'] == id_:
            item['past'] = datetime.now(
                pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")
            item['span'] = 'complete'
            item['next'] = ''
            item['end'] = get_now("%m/%d")(exchange)
    return exchange


async def simple_update_success_count(exchange):
    now = now_str("%Y/%m/%d")
    id_ = int(exchange.get_header('id'))
    for item in exchange.get_body():
        if item['id'] == id_:
            if now == item.get('next', ''):
                if now != item.get('prev_sc', ''):
                    cnt_sc = item.get('cnt_sc', 0)
                    item['cnt_sc'] = cnt_sc + 1
                    item['prev_sc'] = now
            else:
                item['cnt_sc'] = 0
                item['prev_sc'] = now
    return exchange


async def simple_update_success_count_to_none(exchange):
    id_ = int(exchange.get_header('id'))
    for item in exchange.get_body():
        if item['id'] == id_:
            if 'cnt_sc' in item:
                del item['cnt_sc']
            if 'prev_sc' in item:
                del item['prev_sc']
    return exchange

(Aiohttp('/antenna')
    .to(cache_get_processor)
    .to(jinja2_({
        'template': 'antenna.html',
        'data': {
            'items': body(),
            'span_list': span_option
        },
        'util': create_util
    }))
) #yapf: disable

async def merge_item(exchange):
    id_ = int(exchange.get_header('id', '-1'))
    for index, item in enumerate(exchange.get_body()):
        if item['id'] == id_:
            exchange.get_headers().update(item)
            exchange.set_header('index', index)
            break
    exchange.set_body('success')
    return exchange

(RouteId('common_post_processing')
    .process(sort_func)
    .to(cache_set_processor)
    .to(merge_item)
) #yapf: disable

(Context('create-item')
    .to(cache_get_processor)
    .process(lambda ex: ex.set_header('id', max([item.get('id', 0) for item in ex.get_body()]) + 1))
    .process(lambda ex: ex.set_body(
        [calc_date_from_span({**(ex.get_headers(['id', 'name', 'url', 'memo', 'decide', 'span'])), 'start': get_now("%m/%d")(ex)}, True)]
            + ex.get_body()))
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('click-current-item-no-finish')
    .to(cache_get_processor)
    .to(simple_update_success_count)
    .to(simple_update_next())
    .to(simple_update_time)
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('click-current-item-to-finish')
    .to(cache_get_processor)
    .to(complete_item)
    .to(direct('common_post_processing'))
) #yapf: disable

(Context(['click-future-item','click-future-external-link'])
    .to(cache_get_processor)
    .to(simple_update_next(True))
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('reserve-item')
    .to(cache_get_processor)
    .to(simple_update_success_count_to_none)
    .to(simple_update_next())
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('delete-item')
    .to(cache_get_processor)
    .process(lambda ex:
        [item for item in ex.get_body()
            if item['id'] != int(ex.get_header('id'))])
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('get-item-detail')
    .to(cache_get_processor)
    .process(lambda ex: ex.set_headers(
        next((item for item in ex.get_body()
              if item['id'] == int(ex.get_header('id'))), None)))
    .process(lambda ex: ex.set_body('success'))
) #yapf: disable

(Context('update-item-no-finish')
    .to(cache_get_processor)
    .to(simple_update_item)
    .to(direct('common_post_processing'))
) #yapf: disable

(Context('update-item-to-finish')
    .to(cache_get_processor)
    .to(simple_update_item)
    .to(complete_item)
    .to(direct('common_post_processing'))
) #yapf: disable

try:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='public/static')
except:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='../public/static')

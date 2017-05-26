import asyncio
import os
from urllib.parse import urlparse
from consumer import Aiohttp, Any, To, RouteId, Client
from components import cache, direct, log, redis_cache, jinja2_, redirect
from evaluator import set_body, body, header, exists, isEqualTo
from cachetools import LRUCache
from settings.antenna_settings import span_option, span_sort_score
from utility.jinja2_util import create_util
from utility.datetime_util import calc_date_from_span, now_str
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

def get_now(fmt):
    def now_func(exchange):
        return now_str(fmt)

    return now_func


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


async def update_time(exchange):
    if exchange.get_header('reserve', '') != 'true' and (
            exchange.get_header('current', '') != 'true' or
            exchange.get_header('span') == 'complete'
    ) and not exchange.get_header('time_no_update', False):
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
                    'span_list': span_option
                    },
                'env': {
                    'now':get_now("%Y/%m/%d %H:%M")
                },
                'util': create_util
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
    update_success_count(item, headers)
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
        item['decide'] = exchange.get_header('decide')
    if exchange.get_header('finish',
                           'false') == 'true' or item['span'] == 'complete':
        exchange.set_header('time_no_update', False)
        item['span'] = 'complete'
        item['next'] = ''
        if 'end' not in item:
            item['end'] = get_now("%m/%d")(exchange)
    elif span_changed_flag:
        current = exchange.get_header('current', 'false')
        calc_date_from_span(item, current == 'true')
    return item


def update_success_count(item, headers):
    if len(
            headers
    ) <= 3 and 'current' not in headers and 'finish' not in headers and item.get(
            'span') not in ['once', 'primary', 'sometime']:
        now = now_str("%Y/%m/%d")
        if headers.get('reserve', '') != 'true' and now == item.get(
                'next', ''):  # 成功維持条件
            if now != item.get('prev_sc', ''):  # カウントアップ条件
                cnt_sc = item.get('cnt_sc', 0)
                item['cnt_sc'] = cnt_sc + 1
                item['prev_sc'] = now
        else:  # 失敗処理
            item['cnt_sc'] = 0
            item['prev_sc'] = now

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
    .process(lambda ex: ex.set_header('id', max([item.get('id', 0) for item in ex.get_body()]) + 1))
    .process(lambda ex: ex.set_body(
            [calc_date_from_span({**(ex.get_headers(['id','name','url','memo','decide','span'])), 'start': get_now("%m/%d")(ex)}, True)]
            + ex.get_body()))
) #yapf: disable


(Client('/antenna-exchange')
    .to(cache_get_processor)
    .to(direct('antenna_crud'))
    .process(lambda ex: ex.set_body('success'))
) #yapf: disable

def detail(exchange):
    id_ = exchange.get_header('id')
    filtered = [item for item in exchange.get_body() if str(item['id']) == id_]
    if len(filtered) > 0:
        exchange.set_headers(filtered[0])


(Client('/antenna-item')
    .to(cache_get_processor)
    .process(detail)
    .process(lambda ex: ex.set_body('success'))) #yapf: disable

try:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='public/static')
except:
    Aiohttp().application().router.add_static(
        prefix='/public/static', path='../public/static')

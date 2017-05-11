from consumer import Aiohttp, Any, To, RouteId
from components import cache, direct, aiohttp_request, log, soup, zipper
from evaluator import header, body, set_body, get_header
import re
from cachetools import LRUCache
ameblo_cache = LRUCache(maxsize=1000)

#yapf:disable
(Aiohttp('/ameblo-images')
    .validate({
        'rule': lambda ex: re.match('^https://ameblo.jp/.+/$', ex.get_header('url','')),
        'message':'urlパラメータに有効なameblo urlをセットしてください。書式: https://ameblo.jp/{userid}/'})

    .to(cache({
        'cache_object': ameblo_cache,
        'keys': [header('url')],
        'to': Any()
            .throttle(1)
            .to(cache({
                'cache_object': ameblo_cache,
                'keys': [header('url')],
                'to': To(direct('ameblo_images_main'))
                }))
        }))
)

#yapf:disable
(RouteId('ameblo_images_main')
    .validate({
        'process_rule': To(aiohttp_request({'url': header('url'), 'isValid': True})),
        'message': 'amebloサーバーからのレスポンスに問題があるため、処理を中断しました。ameblo idおよびamebloサーバーのステータスを確認してください。'
    })

    .to(log({'name':'ameblo_images_main_start','header':True, 'body': False}))
    # get entrylist last url: max=10
    .to(aiohttp_request({'url':lambda ex: '{}entrylist-10.html'.format(ex.get_header('url'))}))
    .to(soup(lambda soup:(soup.find('a', class_='pagingPrev') or
                     soup.find('a', class_='previousPage') or
                     soup.find('a', class_='skin-paginationPrev') or
                     soup.new_tag("a", href="entrylist-1.html")).get('href')))

    # set entrylist url: entrylist-1.html, entrylist-2.html,...
    .process(lambda ex:[
        '{}entrylist-{}.html'.format(ex.get_header('url'), i)
        for i in range(1, int(ex.get_body().split('entrylist-')[1].split('.')[0]) + 2)
        ])

    # open zipfile
    .to(zipper({
        'mode':'open',
        'zip_file_name': lambda ex: '../public/tmp/ameblo_images/{}.zip'
            .format(ex.get_header('url').split('/')[-2])}))

    .process_with_queue({
        'channels': {
            # channel_1: get entry page url from entrylist and put queue to channel_2
            'channel_1': To(aiohttp_request())
                .to(soup(lambda soup: [element.get('href')
                        for element in soup.find_all('a',
                            href=re.compile('https://ameblo\.jp/.*?/entry-\d+\.html$'),
                            text=re.compile('.'))]))

                .put_queue('channel_2', queue_name='myqueue', unique=True),

            # channel_2: get image url from entry page and put queue to channel_3
            'channel_2': To(aiohttp_request())
                .to(soup(lambda soup:[element.get('src')
                        for element in soup.find_all("img",
                            src=re.compile("^http.*user_images.*?/o"))]))

                .put_queue('channel_3', queue_name='myqueue'),

            # channel_3: get image from image url and write to zip
            'channel_3':To(aiohttp_request({'response_type':'data'}))
                .to(zipper({
                    'mode': 'write',
                    'file_name': lambda ex:'{}_{}'
                        .format(*(ex.get_header('request_url').split('?')[0].split('/')[i] for i in [-7, -1]))
                }))
        },
        'init_queue': {
            'channel_1':body()
        },
        'queue_name': 'myqueue',
        'maxsize': 30
    })
    .to(zipper({'mode':'close'}))
    .process(set_body(get_header('zip_file_name')))
    .to(log({'name':'ameblo_images_main_end'}))
 )

Aiohttp().application().router.add_static(
    prefix='/public/tmp', path='../public/tmp')

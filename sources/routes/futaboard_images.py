from consumer import Aiohttp, Any, To, RouteId
from components import cache, direct, aiohttp_request, log, soup, zipper
from evaluator import header, body
import re
from cachetools import LRUCache
futaboard_cache = LRUCache(maxsize=1000)

#yapf:disable
(Aiohttp('/futaboard-images')
    .validate({
        'rule': lambda ex: re.match('^http://board.futakuro.com/jk2/res/\d+.htm$', ex.get_header('url','')),
        'message':'urlパラメータに有効なふたボード urlをセットしてください。書式: http://board.futakuro.com/jk2/res/{id}.htm$'})

    .to(cache({
        'cache_object': futaboard_cache,
        'keys': [header('url')],
        'to': Any()
            .throttle(1)
            .to(cache({
                'cache_object': futaboard_cache,
                'keys': [header('url')],
                'to': To(direct('futaboard_images_main'))
                }))
        }))
)

#yapf:disable
(RouteId('futaboard_images_main')
    .validate({
        'process_rule': To(aiohttp_request({'url': header('url'), 'isValid': True})),
        'message': 'futaboardサーバーからのレスポンスに問題があるため、処理を中断しました。urlおよびfutaboardサーバーのステータスを確認してください。'
    })

    .to(log({'name':'futaboard_images_main_start','header':True, 'body': False}))
    .to(aiohttp_request({'url': header('url')}))
    .to(soup(lambda soup:[span.find('a').get('href') if 'http://' in span.find('a').get('href') else 'http://board.futakuro.com/jk2/' + span.find('a').get('href') for span in soup.find_all('span', class_='s10')]))
    # open zipfile
    .to(zipper({
        'mode':'open',
        'zip_file_name': lambda ex: '../public/tmp/futaboard_images/{}.zip'
            .format(ex.get_header('url').split('/')[-1].split('.')[0])}))

    .process_with_queue({
        'channels': {
            'channel_1':To(aiohttp_request({'response_type':'data'}))
                .to(zipper({
                    'mode': 'write',
                    'file_name': lambda ex: ex.get_header('request_url').split('/')[-1]
                }))
        },
        'init_queue': {
            'channel_1':body()
        },
        'maxsize': 30
    })
    .to(zipper({'mode':'close'}))
    .update_exchange({'body': header('zip_file_name')})
    .to(log({'name':'futaboard_images_main_end'}))
)

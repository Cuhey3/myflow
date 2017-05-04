from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *
import re

(Aiohttp('/ameblo-images').to(direct('ameblo_images')))

(RouteId('ameblo_images')
    .to(log({'name':'ameblo_images_route_start'}))

    # get entrylist last url: max=20
    .to(aiohttp_request({'url':lambda ex: '{}entrylist-20.html'.format(ex.get_header('url'))}))
    .to(soup(lambda soup:(soup.find('a', class_='pagingPrev') or
                     soup.find('a', class_='previousPage') or
                     soup.find('a', class_='skin-paginationPrev')).get('href')))

    # set entrylist url: entrylist-1.html, entrylist-2.html,...
    .process(lambda ex:['{}entrylist-{}.html'.format(ex.get_header('url'), i)
        for i in range(1, int(ex.get_body().split('entrylist-')[1].split('.')[0]) + 2)])

    # start queue process
    .to(log({'name':'ameblo_images_queue_process_start'}))

    # open zipfile
    .to(zipper({
        'mode':'open',
        'zip_file_name': lambda ex: '../public/tmp/ameblo_images/{}.zip'
            .format(ex.get_header('url').split('/')[-2])}))

    .process_with_queue({
        'channels': {
            # channel_1: get entry page url from entrylist and put queue to channel_2
            'channel_1': To(aiohttp_request())
                .to(soup(lambda soup: soup.find_all('a',
                    href=re.compile('https://ameblo\.jp/.*?/entry-\d+\.html$'),
                    text=re.compile('.')), attr='href'))
                .put_queue('channel_2', queue_name='myqueue',unique=True),

            # channel_2: get image url from entry page and put queue to channel_3
            'channel_2': To(aiohttp_request())
                .to(soup(lambda soup:soup.find_all(
                    "img", src=re.compile("^http.*user_images.*?/o")),attr='src'))
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
        'maxsize': 20
    })
    .to(zipper({'mode':'close'}))
    .update_exchange({'body': header('zip_file_name')})
    .to(log({'name':'ameblo_images_queue_process_end'}))
 )

Aiohttp().application().router.add_static(
    prefix='/public/tmp', path='../public/tmp')

Aiohttp().run()

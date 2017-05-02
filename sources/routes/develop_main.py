import asyncio
from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *
#from routes.test_routes import tasks_main

import aiohttp
from aiohttp import web
from multidict import MultiDict

from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and attrs[0][1].startswith('src/'):
            self.data[attrs[0][1]] = True


#    def handle_endtag(self, tag):
#        print("Encountered an end tag :", tag)

#    def handle_data(self, data):
#        print("Encountered some data  :", data)


async def process_1(exchange):
    url = exchange.get_header('url')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(resp.status)
            text = await resp.text()
            parser = MyHTMLParser()
            parser.feed(text)
            exchange.set_header('url_list', list(parser.data.keys()))
            print('img size is...', len(exchange.get_header('url_list')))
            from io import BytesIO
            inMemoryOutputFile = BytesIO()
            exchange.set_body(inMemoryOutputFile)
            from zipfile import ZipFile
            import zipfile
            exchange.set_header(
                'zipfile',
                #                                ZipFile(inMemoryOutputFile, 'w',
                ZipFile('../public/tmp/foo.zip', 'w', zipfile.ZIP_DEFLATED))
            return exchange


async def process_2(exchange):
    image_url = 'http://board.futakuro.com/jk2/' + exchange.get_body()
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            split = image_url.split('/')
            data = await resp.read()
            file_name = split[len(split) - 1]
            exchange.parent().get_header('zipfile').writestr(file_name, data)
            return exchange


async def process_3(exchange):
    zipFile = exchange.get_header('zipfile')
    zipFile.close()
    inMemoryOutputFile = exchange.get_body()
    inMemoryOutputFile.seek(0)
    return exchange


#(RouteId('get_zip').process(lambda exchange: exchange.set_body('boo')))
(RouteId('get_zip').to(process_1).split(header('url_list'),
                                        To(process_2)).to(process_3))


async def foo(request):
    exchange = await Endpoints().send_to(
        'get_zip', Exchange(header={'url': request.rel_url.query['url']}))
    return web.Response(text='foo')
    '''
    headers=MultiDict({
        'Content-Disposition':
        'Attachment;filename=poyoyon.zip'
    }),
    body=exchange.get_body())
    '''
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'http://www.rd.com/wp-content/uploads/sites/2/2016/04/01-cat-wants-to-tell-you-laptop.jpg'
        ) as resp:
            async with session.get(
                'https://cdn.kinsights.com/cache/2f/a0/2fa05bebbd843b9aa91e348a7e77d5c2.jpg'
            ) as resp2:
                boo = await resp.read()
                boo2 = await resp2.read()
                from zipfile import ZipFile
                import zipfile
                from io import BytesIO

                inMemoryOutputFile = BytesIO()

                zipFile = ZipFile(inMemoryOutputFile, 'w',
                                  zipfile.ZIP_DEFLATED)
                zipFile.writestr('OEBPS/content.jpg', boo)
                zipFile.writestr('OEBPS/content2.jpg', boo2)
                zipFile.close()
                print(zipFile)
                inMemoryOutputFile.seek(0)
                dir(inMemoryOutputFile)
                return web.Response(
                    headers=MultiDict({
                        'Content-Disposition':
                        'Attachment;filename=poyoyon.zip'
                    }),
                    body=inMemoryOutputFile)
    '''


(RouteId('foo').process_with_queue({
    'queues': {
        'queue_1': To(foo('')).split(body(), Any().put_queue('queue_2', body())),
        'queue_2': To(bar('')).put_queue('queue_3', body()),
        'queue_3': To(wao(''))
    },
    'init_queue': {
        'queue_1': ['http://ja.wikipedia/org']
    }
})) #yapf: disable
app = web.Application()
app.router.add_get('/boo', foo)
app.router.add_static(prefix='/tmp', path='../public/tmp')
web.run_app(app)

#asyncio.get_event_loop().run_until_complete(tasks_main())
'''
#yapf:disable
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
#yapf:enable
if exchange:
    print(exchange.get_body())
'''

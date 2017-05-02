import asyncio
from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *
from bs4 import BeautifulSoup
import aiohttp


async def get_entrypages(exchange):
    async with aiohttp.ClientSession() as session:
        async with session.get(exchange.get_body() +
                               'entrylist-10000.html') as resp:
            soup = BeautifulSoup(await resp.text(), 'lxml')
            import re
            last_page_url = (
                soup.find('a', class_='pagingPrev') or
                soup.find('a', class_='previousPage') or
                soup.find('a', class_='skin-paginationPrev')).get('href')
            m = re.search('(?<=entrylist-)(\d+)', last_page_url)
            exchange.set_body([
                exchange.get_body() + 'entrylist-' + str(i) + '.html'
                for i in range(1, int(m.group(1)) + 2)
            ])
            return exchange


async def get_pages(exchange):
    async with aiohttp.ClientSession() as session:
        async with session.get(exchange.get_body()) as resp:
            soup = BeautifulSoup(await resp.text(), 'lxml')
            import re

            for element in soup.find_all(
                    'a',
                    href=re.compile('https://ameblo\.jp/.*?/entry-\d+\.html$'),
                    text=re.compile('.')):
                href = element.get('href')
                if href not in exchange.parent().get_header('channel_2_dict'):
                    exchange.parent().get_header('channel_2_dict')[href] = True
                    await exchange.parent().get_header('queues').get(
                        'myqueue').put(('channel_2', href))


async def page_parse(exchange):
    print(exchange.get_body())
    async with aiohttp.ClientSession() as session:
        async with session.get(exchange.get_body()) as resp:
            soup = BeautifulSoup(await resp.text(), 'lxml')
            import re

            for element in soup.find_all(
                    "img", src=re.compile("^http.*user_images.*?/o")):
                await exchange.parent().get_header('queues').get(
                    'myqueue').put(('channel_3', element.get('src')))

    return exchange

(RouteId('myqueue')
    .process(lambda ex: ex.set_header('result',[]))
    .process(lambda ex: ex.set_header('channel_2_dict',{}))
    .to(get_entrypages)
    .process_with_queue({
        'channels': {
            'channel_1': Any().to(get_pages),
            'channel_2': To(log()).to(page_parse),
            'channel_3': To(log()).process(lambda ex:ex.parent().get_header('result').append(ex.get_body()))
        },
        'init_queue': {
            'channel_1':body()
        },
        'queue_name': 'myqueue',
        'maxsize': 50
}))#yapf: disable

async def foo():
    exchange = await Endpoints().send_to(
        #'myqueue', Exchange('https://ameblo.jp/iris-official-blog/', {}))
        'myqueue',
        #Exchange('https://ameblo.jp/misawa-sachika/', {}))
        Exchange('https://ameblo.jp/00dpd/', {}))
    print(exchange.get_body())
    #    print(exchange.get_header('result'))
    print(len(exchange.get_header('result')))


asyncio.get_event_loop().run_until_complete(foo())

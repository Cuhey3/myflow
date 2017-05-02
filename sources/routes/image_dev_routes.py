import asyncio
from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *
from bs4 import BeautifulSoup
import aiohttp

#from routes.test_routes import tasks_main
(RouteId('myqueue')
    .process(lambda ex: ex.set_header('result',[]))
    .process(lambda ex: ex.set_header('queue_2_dict',{}))
    .to(get_entrypages)
    .process_with_queue({
        'queues': {
            'queue_1': Any().to(get_pages),
            'queue_2': To(log()).to(page_parse),
            'queue_3': To(log()).process(lambda ex:ex.parent().get_header('result').append(ex.get_body()))
        },
        'init_queue': {
            'queue_1': body()
        }
}))#yapf: disable

import asyncio
from consumer import *
from endpoints import Endpoints
from exchange import Exchange
from components import *
from evaluator import *
from routes.test_routes import tasks_main

asyncio.get_event_loop().run_until_complete(tasks_main())
asyncio.get_event_loop().run_forever()
'''
#yapf:disable
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
exchange = Endpoints().send_to('myfoo',Exchange("poko",{'foo': 'bar','pon': {'puu': 'poo'}}))
#yapf:enable
if exchange:
    print(exchange.get_body())
'''

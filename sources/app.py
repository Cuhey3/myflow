from consumer import *
from routes import markdown_route
## TBD: await Aiohttp().run()
Aiohttp().application().router.add_static(
    prefix='/public/static', path='../public/static')
Aiohttp().run()

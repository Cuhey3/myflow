from aiohttp import web


async def handler(request):
    return web.Response(text='foo')


app = web.Application()
app.router.add_route('GET', '/foo', handler)
web.run_app(app, host='0.0.0.0', port=8080)
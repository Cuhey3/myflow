from producer import Producer
from custom_processor import *


class Consumer(Producer):
    def __init__(self, processor=None, consumer=None):
        super().__init__(processor, self)

    async def consume(self, exchange):
        return await self.produce(exchange)


class To(Consumer):
    def __init__(self, processor):
        super().__init__(processor, self)


class Any(Consumer):
    def __init__(self):
        super().__init__(None, self)


class RouteId(Consumer):
    def __init__(self, route_id):
        super().__init__(None, self)
        from endpoints import Endpoints
        Endpoints().put_endpoint(route_id, self)


class Timer(Consumer):
    def __init__(self, timer_param={}):
        super().__init__(None, self)
        from timer_core import TimerCore
        timer_core = TimerCore(timer_param)
        if timer_core.isEnable():
            from exchange import Exchange
            import asyncio
            loop = asyncio.get_event_loop()

            async def processor(exchange):
                await timer_core.initialDelay()
                loop.create_task(self.produce(exchange))
                async for t in timer_core:
                    loop.create_task(self.produce(exchange))

            loop.create_task(processor(Exchange(None, {})))


class Process(Consumer):
    def __init__(self, func):
        async def async_func(exchange):
            func(exchange)
            return exchange

        super().__init__(async_func, self)


class Aiohttp(Consumer):
    __web_application = None

    def __init__(self, uri=None):
        if Aiohttp.__web_application is None:
            from aiohttp import web
            Aiohttp.__web_application = web.Application()
        if uri:
            super().__init__(None, self)

            async def handle(request):
                header = {}
                for key in request.match_info:
                    header[key] = request.match_info.get(key)
                for key in request.rel_url.query:
                    header[key] = request.rel_url.query.get(key)
                exchange = await self.produce(Exchange({}, header))
                text = exchange.get_body()
                content_type = exchange.get_header('content-type')
                return web.Response(text=text, content_type=content_type)

            self.application().router.add_get(uri, handle)

    def application(self):
        return self.__web_application

    def run(self):
        import os
        from aiohttp import web
        port = int(os.environ.get('PORT', 8080))
        web.run_app(self.__web_application, host='0.0.0.0', port=port)


class Composer(Consumer):
    __composer_mapping = None

    def __init__(self, params=None):
        if Composer.__composer_mapping is None:
            Composer.__composer_mapping = {}
        if params:
            super().__init__(None, self)
            composer_id = params.get('id')
            Composer.__composer_mapping[composer_id] = self
            self.compose = params.get('compose')
            self.sources = {item: False for item in params.get('from')}

    async def send_to(self, composer_id, source_name, exchange):
        composer = Composer.__composer_mapping.get(composer_id)
        if source_name in composer.sources:
            composer.sources[source_name] = exchange
            values = [v for k, v in composer.sources.items()]
            if all(values):
                exchange.set_body(composer.compose(values))
                await composer.produce(exchange)

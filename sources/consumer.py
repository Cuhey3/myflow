from producer import Producer
from custom_processor import *
from aiohttp import web


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


class Context(Consumer):
    __context_dict = None
    __context_id_name = None

    def __init__(self, context_param=None):
        if Context.__context_dict is None:
            Context.__context_dict = {}
            Context.__context_id_name = {}

            async def handle(request):
                obj = await request.json()
                exchange = Exchange(obj['body'], obj['header'])
                context_name = exchange.get_header(
                    '__context_name'
                ) or Context.__context_id_name[exchange.get_header(
                    '__context_id')]
                print(context_name)
                exchange = await Context.__context_dict.get(context_name
                                                            ).produce(exchange)
                return web.Response(
                    text=exchange.to_json(), content_type='application/json')

            Aiohttp().application().router.add_post(self.path(), handle)

        if context_param:
            super().__init__(None, self)
            if isinstance(context_param, dict):
                Context.__context_dict[context_param.get('name')] = self
                Context.__context_id_name = {**Context.__context_id_name, context_param['id']: context_param('name')}
            elif isinstance(context_param, list):
                for name in context_param:
                    Context.__context_dict[name] = self
            elif isinstance(context_param, str):
                Context.__context_dict[context_param] = self

    def path(self):
        return '/context'


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

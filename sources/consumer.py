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


#TBD: Aiohttp

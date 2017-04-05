from custom_processor import *


class Producer():
    def __init__(self, processor=None, previous_producer=None):
        self.previous_producer = previous_producer
        self.next_producer = None
        self.processor = processor
        self.custom_processor = []

    def to(self, processor):
        self.next_producer = Producer(processor, self)
        return self.next_producer

    def when(self, routes, otherwise_processor=None):
        self.custom_processor.append(
            ContentBasedProcessor(routes, otherwise_processor))
        return self

    def filter(self, predicate):
        self.custom_processor.append(FilterProcessor(predicate))
        return self

    def split(self, expression, producer):
        self.custom_processor.append(SplitProcessor(expression, producer))
        return self

    def gather(self, processors, gather_func):
        self.custom_processor.append(GatherProcessor(processors, gather_func))
        return self

    def first_producer(self):
        if self.previous_producer:
            return self.previous_producer.first_producer()
        else:
            return self

    async def produce(self, exchange):
        if exchange and self.processor:
            exchange = await self.processor(exchange)
        if exchange:
            for processor in self.custom_processor:
                exchange = await processor.process(exchange)
                if not exchange:
                    break
            if exchange:
                if self.next_producer:
                    exchange = await self.next_producer.produce(exchange)
        return exchange


class RouteId(Producer):
    def __init__(self, route_id):
        super().__init__()
        from endpoints import Endpoints
        Endpoints().put_endpoint(route_id, self)


class To(Producer):
    def __init__(self, processor):
        self.previous_producer = None
        self.next_producer = None
        self.processor = processor
        self.custom_processor = []


class Timer(Producer):
    def __init__(self, timer_param):
        self.previous_producer = None
        self.next_producer = None
        self.processor = None
        self.custom_processor = []
        from timer_core import TimerCore
        timer_core = TimerCore(timer_param)
        if timer_core.isEnable():
            from exchange import Exchange
            import asyncio
            loop = asyncio.get_event_loop()

            async def process(exchange):
                await timer_core.initialDelay()
                loop.create_task(self.produce(exchange))
                async for t in timer_core:
                    loop.create_task(self.produce(exchange))

            loop.create_task(process(Exchange(None, {})))

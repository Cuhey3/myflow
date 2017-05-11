from custom_processor import *


class Producer():
    def __init__(self, processor=None, consumer=None):
        self.next_producer = None
        self.processor = processor
        self.consumer = consumer
        self.custom_processor = []

    def to(self, processor):
        self.next_producer = Producer(processor, self.consumer)
        return self.next_producer

    def when(self, routes):
        self.custom_processor.append(ContentBasedProcessor(routes))
        return self

    def filter(self, predicate):
        self.custom_processor.append(FilterProcessor(predicate))
        return self

    def split(self, params):
        self.custom_processor.append(SplitProcessor(params))
        return self

    def gather(self, processors, gather_func):
        self.custom_processor.append(GatherProcessor(processors, gather_func))
        return self

    def get_consumer(self):
        return self.consumer

    def process(self, func):
        self.custom_processor.append(LambdaProcessor(func))
        return self

    def process_with_queue(self, params):
        self.custom_processor.append(WithQueueProcessor(params))
        return self

    def put_queue(self,
                  channel_name,
                  expression=None,
                  queue_name='default_queue',
                  unique=False):
        self.custom_processor.append(
            PutQueueProcessor(channel_name, expression, queue_name, unique))
        return self

    def update_exchange(self, params):
        self.custom_processor.append(UpdateExchangeProcessor(params))
        return self

    def validate(self, params):
        self.custom_processor.append(ValidateProcessor(params))
        return self

    def throttle(self, throttle_size):
        self.custom_processor.append(ThrottleProcessor(throttle_size))
        return self

    def assert_(self, *args):
        self.custom_processor.append(AssertProcessor(*args))
        return self

    def sleep(self, num):
        self.custom_processor.append(SleepProcessor(num))
        return self

    async def produce(self, exchange):
        try:
            throttle_processors = []
            if not exchange.get_header('validate', True):
                return exchange
            if exchange and self.processor:
                exchange = await self.processor(exchange)
            if exchange:
                for processor in self.custom_processor:
                    if isinstance(processor, ThrottleProcessor):
                        throttle_processors.append(processor)
                    exchange = await processor.processor(exchange)
                    if not exchange:
                        break
                    if not exchange.get_header('validate', True):
                        break
                if exchange:
                    if self.next_producer:
                        exchange = await self.next_producer.produce(exchange)
        finally:
            for processor in throttle_processors:
                await processor.consume()
        return exchange

    def send_to_sync(self, exchange=Exchange()):
        return asyncio.get_event_loop().run_until_complete(
            self.get_consumer().produce(exchange))

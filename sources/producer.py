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

    def get_consumer(self):
        from consumer import Consumer
        return self.consumer

    def process(self, func):
        self.custom_processor.append(LambdaProcessor(func))
        return self

    def process_with_queue(self, params):
        self.custom_processor.append(WithQueueProcessor(params))
        return self

    def put_queue(self, queue_name, expression=None):
        self.custom_processor.append(PutQueueProcessor(queue_name, expression))
        return self

    async def produce(self, exchange):
        if exchange and self.processor:
            exchange = await self.processor(exchange)
        if exchange:
            for processor in self.custom_processor:
                exchange = await processor.processor(exchange)
                if not exchange:
                    break
            if exchange:
                if self.next_producer:
                    exchange = await self.next_producer.produce(exchange)
        return exchange

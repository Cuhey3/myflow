#exchangeが妥当かのチェックはここではせずProducer.produceで行う
from exchange import Exchange
import asyncio


class ContentBasedProcessor():
    def __init__(self, routes, otherwise_producer):
        def __select_consumer(exchange):
            for predicate, producer in routes:
                if callable(predicate) and predicate(exchange) == True:
                    return producer.get_consumer()
                elif predicate == True:
                    return producer.get_consumer()
            else:
                if otherwise_producer:
                    return otherwise_producer.get_consumer()

        self.__select_consumer = __select_consumer

    async def processor(self, exchange):
        consumer = self.__select_consumer(exchange)
        from consumer import Consumer
        if isinstance(consumer, Consumer):
            exchange = await consumer.consume(exchange)
            return exchange
        return False


class FilterProcessor():
    def __init__(self, predicate):
        def __filter(exchange):
            if callable(predicate):
                return predicate(exchange)
            elif predicate:
                return predicate

        self.__filter = __filter

    async def processor(self, exchange):
        if self.__filter(exchange):
            return exchange
        else:
            return False


class SplitProcessor():
    # TBD:aggregation_strategy=None
    def __init__(self, expression=None, producer=None):
        async def split_processor(exchange):
            from producer import Producer
            assert isinstance(producer, Producer), 'split processor requires Producer.' #yapf: disable
            import copy
            if callable(expression):
                to_split = expression(exchange)
            else:
                to_split = copy.deepcopy(exchange).get_body()
            consumer = producer.get_consumer()
            from consumer import Consumer
            assert isinstance(consumer, Consumer), 'Consumer is not set in Producer for split processor.' #yapf: disable
            import collections
            if isinstance(to_split, str):
                to_split = to_split.split()
            assert (isinstance(to_split, collections.Iterable))
            await asyncio.gather(* [
                consumer.produce(exchange.create_child(Exchange(sp)))
                for sp in to_split
            ])

        self.split_processor = split_processor

    async def processor(self, exchange):
        await self.split_processor(exchange)
        return exchange


class GatherProcessor():
    def __init__(self, producers, gather_func):
        assert isinstance(producers, list), 'gathering producers must be list.' #yapf: disable
        async def gather_processor(exchange):
            coroutines = map(lambda producer: producer.get_consumer().produce(exchange.create_child()), producers)
            await asyncio.gather(*coroutines)
            return gather_func(exchange.children)

        self.gather_processor = gather_processor

    async def processor(self, exchange):
        return await self.gather_processor(exchange)


class LambdaProcessor():
    def __init__(self, func):
        assert callable(func), 'argument passed to the process must be a function.' #yapf: disable

        async def lambda_processor(exchange):
            func(exchange)
            return exchange

        self.lambda_processor = lambda_processor

    async def processor(self, exchange):
        return await self.lambda_processor(exchange)


class WithQueueProcessor():
    def __init__(self, params):
        assert 'channels' in params, 'channels parameter is required.'
        loop = asyncio.get_event_loop()
        channels = params.get('channels')

        async def with_queue_processor(exchange):
            prepare_queue = asyncio.Queue(
                loop=loop, maxsize=params.get('maxsize', 0))
            task_queue = asyncio.Queue(loop=loop)
            from evaluator import evaluate_expression
            init_queues = evaluate_expression(
                params.get('init_queue', {}), exchange)

            async def init_queue(exchange):
                for channel_name in init_queues:
                    init_queue = init_queues.get(channel_name, [])
                    for q in init_queue:
                        await task_queue.put((channel_name, q))

            await init_queue(exchange)
            queues = exchange.get_header('queues', {})
            queues[params.get('queue_name', 'default_queue')] = task_queue
            exchange.set_header('queues', queues)

            async def create_task(task):
                channel = task[0]
                body = task[1]
                child = exchange.create_child()
                child.set_body(body)
                await channels.get(channel).produce(child)
                await prepare_queue.get()
                if task_queue.empty() and prepare_queue.empty():
                    await task_queue.put(None)
                else:
                    print(task_queue.qsize(), prepare_queue.qsize())

            while True:
                task = await task_queue.get()
                if task is None:
                    break
                await prepare_queue.put('')

                loop.create_task(create_task(task))
            return exchange

        self.with_queue_processor = with_queue_processor

    async def processor(self, exchange):
        return await self.with_queue_processor(exchange)


class PutQueueProcessor():
    def __init__(self,
                 channel_name,
                 expression=None,
                 queue_name='default_queue'):
        from evaluator import evaluate_expression

        async def put_queue_processor(exchange):
            if expression is None:
                value = exchange.get_body()
            else:
                value = evaluate_expression(expression, exchange)
            await exchange.parent().get_header('queues').get(queue_name).put(
                (channel_name, value))
            return exchange

        self.put_queue_processor = put_queue_processor

    async def processor(self, exchange):
        return await self.put_queue_processor(exchange)


def set_body(expression):
    async def processor(exchange):
        from evaluator import evaluate_expression
        exchange.set_body(evaluate_expression(expression, exchange))
        return exchange

    return processor


def set_header(key, expression):
    async def processor(exchange):
        from evaluator import evaluate_expression
        exchange.set_header(key, evaluate_expression(expression, exchange))
        return exchange

    return processor


def to_json(expression=None):
    async def processor(exchange):
        from evaluator import evaluate_expression
        #yapf: disable
        to_dumps = exchange.get_body() if expression is None else evaluate_expression(expression, exchange)
        import json
        exchange.set_body(json.dumps(to_dumps))
        return exchange

    return processor


# TBD:routingSlip
# class RoutingSlipProcessor():

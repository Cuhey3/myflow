from exchange import Exchange
import asyncio
from evaluator import evaluate_expression, body
loop = asyncio.get_event_loop()


class ContentBasedProcessor():
    def __init__(self, routes):
        def __select_consumer(exchange):
            for predicate, producer in routes:
                if (callable(predicate) and
                        predicate(exchange) == True) or predicate == True:
                    return producer.get_consumer()

        self.__select_consumer = __select_consumer

    async def processor(self, exchange):
        consumer = self.__select_consumer(exchange)
        if consumer is None:
            return False
        else:
            return await consumer.consume(exchange)


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
    def __init__(self, params):
        from_ = params.get('from') or body()
        to = params.get('to', None)
        aggregate = params.get('aggregate', None)
        assert to is not None, 'split processor requires to argument.'
        assert aggregate is None or callable(
            aggregate
        ), 'split processor requires aggregate argument as function.'
        consumer = to.get_consumer()

        async def split_processor(exchange):
            import copy
            to_split = evaluate_expression(from_, exchange)
            import collections
            if isinstance(to_split, str):
                to_split = to_split.split()
            assert isinstance(
                to_split,
                collections.Iterable), 'split target is not iterable.'
            gatherd = await asyncio.gather(* [
                consumer.produce(exchange.create_child(Exchange(sp)))
                for sp in to_split
            ])
            if aggregate:
                exchange.set_body(aggregate(gatherd))
            return exchange

        self.split_processor = split_processor

    async def processor(self, exchange):
        return await self.split_processor(exchange)


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
            result = func(exchange)
            if result is not None:
                exchange.set_body(result)
            return exchange

        self.lambda_processor = lambda_processor

    async def processor(self, exchange):
        return await self.lambda_processor(exchange)


class WithQueueProcessor():
    def __init__(self, params):
        assert 'channels' in params, 'channels parameter is required.'
        channels = params.get('channels')

        async def with_queue_processor(exchange):
            task_queue = asyncio.Queue(loop=loop)
            init_queues = evaluate_expression(
                params.get('init_queue', {}), exchange)

            async def init_queue(exchange):
                for channel_name in init_queues:
                    init_queue = init_queues.get(channel_name, [])
                    for q in init_queue:
                        await task_queue.put((channel_name, q))

            await init_queue(exchange)
            if task_queue.empty():
                return exchange

            prepare_queue = asyncio.Queue(
                loop=loop, maxsize=params.get('maxsize', 0))

            queues = exchange.get_header('queues', {})
            queues[params.get('queue_name', 'default_queue')] = task_queue
            exchange.set_header('queues', queues)
            channel_dict = exchange.get_header('channel_dict', {})
            for k in channels:
                channel_dict[k] = {}
            exchange.set_header('channel_dict', channel_dict)

            async def create_task(task):
                channel = task[0]
                body = task[1]
                child = exchange.create_child()
                child.set_body(body)
                await channels.get(channel).get_consumer().produce(child)
                prepare_queue.get_nowait()
                if task_queue.empty() and prepare_queue.empty():
                    await task_queue.put(None)

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
                 queue_name='default_queue',
                 unique=False):
        async def put_queue_processor(exchange):
            if expression is None:
                value = exchange.get_body()
            else:
                value = evaluate_expression(expression, exchange)
            import collections

            def put_queue(v):
                if unique:
                    if not exchange.parent().get_header('channel_dict').get(
                            channel_name).get(v, False):
                        exchange.parent().get_header('channel_dict').get(
                            channel_name)[v] = True
                    else:
                        return False
                exchange.parent().get_header('queues').get(
                    queue_name).put_nowait((channel_name, v))
                return True

            if isinstance(value, collections.Iterable):
                for v in value:
                    put_queue(v)
            else:
                put_queue(value)
            return exchange

        self.put_queue_processor = put_queue_processor

    async def processor(self, exchange):
        return await self.put_queue_processor(exchange)


class UpdateExchangeProcessor():
    def __init__(self, params):
        async def update_exchange_processor(exchange):
            for field_name in params:
                value = evaluate_expression(params[field_name], exchange)
                if field_name == 'body':
                    exchange.set_body(value)
                else:
                    exchange.set_header(field_name, value)
            return exchange

        self.update_exchange_processor = update_exchange_processor

    async def processor(self, exchange):
        return await self.update_exchange_processor(exchange)


class ValidateProcessor():
    def __init__(self, params):
        rule = params.get('rule', None)
        process_rule = params.get('process_rule', None)
        to = params.get('to', None)
        message = params.get('message', None)

        async def validate_processor(exchange):
            if rule:
                if not rule(exchange):
                    exchange.set_header('validate', False)
            elif process_rule:
                exchange = await process_rule.get_consumer().produce(exchange)
            if not exchange.get_header('validate', True):
                if to:
                    exchange = await to.get_consumer().produce(exchange)
                elif message:
                    exchange.set_body(message)
            return exchange

        self.validate_processor = validate_processor

    async def processor(self, exchange):
        return await self.validate_processor(exchange)


class ThrottleProcessor():
    def __init__(self, throttle_size):
        self.throttle_queue = asyncio.Queue(maxsize=throttle_size, loop=loop)

        async def throttle_processor(exchange):
            await self.throttle_queue.put('')
            print('entry throttle queue')
            return exchange

        self.throttle_processor = throttle_processor

    async def processor(self, exchange):
        return await self.throttle_processor(exchange)

    async def consume(self):
        await self.throttle_queue.get()
        print('release throttle queue')


def set_body(expression):
    async def processor(exchange):
        exchange.set_body(evaluate_expression(expression, exchange))
        return exchange

    return processor


def set_header(key, expression):
    async def processor(exchange):
        exchange.set_header(key, evaluate_expression(expression, exchange))
        return exchange

    return processor


def to_json(expression=None):
    async def processor(exchange):
        #yapf: disable
        to_dumps = exchange.get_body() if expression is None else evaluate_expression(expression, exchange)
        import json
        exchange.set_body(json.dumps(to_dumps))
        return exchange

    return processor

# TBD:routingSlip
# class RoutingSlipProcessor():

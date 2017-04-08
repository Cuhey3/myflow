#exchangeが妥当かのチェックはここではせずProducer.produceで行う
from exchange import Exchange


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
            for sp in to_split:
                await consumer.produce(Exchange(sp))

        self.split_processor = split_processor

    async def processor(self, exchange):
        await self.split_processor(exchange)
        return None


class GatherProcessor():
    def __init__(self, producers, gather_func):
        assert isinstance(producers, list), 'gathering producers must be list.' #yapf: disable
        async def gather_processor(exchange):
            import copy
            coroutines = map(lambda producer: producer.get_consumer().produce(copy.deepcopy(exchange)), producers)
            import asyncio
            gathered = await asyncio.gather(*coroutines)
            return gather_func(gathered)

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

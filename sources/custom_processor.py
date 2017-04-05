#exchangeが妥当かのチェックはここではせずProducer.produceで行う
from exchange import Exchange


class ContentBasedProcessor():
    def __init__(self, routes, otherwise_processor):
        def __content_based_processor(exchange):
            for predicate, processor in routes:
                if callable(predicate) and predicate(exchange) == True:
                    return processor.first_producer()
                elif predicate == True:
                    return processor.first_producer()
            else:
                if otherwise_processor:
                    return otherwise_processor.first_producer()

        self.__content_based_processor = __content_based_processor

    async def process(self, exchange):
        selected_producer = self.__content_based_processor(exchange)
        if selected_producer:
            exchange = await selected_producer.produce(exchange)
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

    async def process(self, exchange):
        if self.__filter(exchange):
            return exchange
        else:
            return False


class SplitProcessor():
    # TBD:aggregation_strategy=None
    def __init__(self, expression=None, producer=None):
        async def split_processor(exchange):
            import copy
            top_producer = producer.first_producer()
            if callable(expression):
                to_split = expression(exchange)
            else:
                to_split = copy.deepcopy(exchange).get_body()

            if producer:
                import collections
                if isinstance(to_split, str):
                    to_split = to_split.split()
                assert (isinstance(to_split, collections.Iterable))
                for sp in to_split:
                    await producer.produce(Exchange(sp))

        self.split_processor = split_processor

    async def process(self, exchange):
        await self.split_processor(exchange)
        return None


class GatherProcessor():
    def __init__(self, producers, gather_func):
        assert isinstance(producers, list), 'gathering producers must be list.' #yapf: disable
        async def gather_processor(exchange):
            import copy
            coroutines = map(lambda producer: producer.first_producer().produce(copy.deepcopy(exchange)), producers)
            import asyncio
            gathered = await asyncio.gather(*coroutines)
            return gather_func(gathered)

        self.gather_processor = gather_processor

    async def process(self, exchange):
        return await self.gather_processor(exchange)


# TBD:routingSlip
# class RoutingSlipProcessor():

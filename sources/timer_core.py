import asyncio


class TimerCore():
    def __init__(self, params):
        self.period = params.get('period', 1)
        self.repeatCount = params.get('repeatCount', -1)
        self.delay = params.get('delay', 0)

    def isEnable(self):
        return self.period > 0 and self.delay >= 0

    def countDown(self):
        if self.repeatCount > 0:
            self.repeatCount = self.repeatCount - 1
            if self.repeatCount == 0:
                raise StopAsyncIteration()

    async def initialDelay(self):
        await asyncio.sleep(self.delay)

    async def sleep(self):
        await asyncio.sleep(self.period)

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.countDown()
        await self.sleep()
        return self.period

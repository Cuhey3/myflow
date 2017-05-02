import asyncio

loop = asyncio.get_event_loop()
queue = asyncio.Queue(loop=loop)

queue.put_nowait('foo')
queue.put_nowait('bar')
queue.put_nowait(None)


async def poyoyon():
    while True:
        item = await queue.get()
        if item is None:
            break
        print(item)


##loop.create_task(papaiya())
loop.run_until_complete(poyoyon())

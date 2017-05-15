import asyncio
import aioredis
from urllib.parse import urlparse
import os

loop = asyncio.get_event_loop()

redis_url = urlparse(os.environ['REDIS_URL'])


async def go():
    foo = aioredis.create_connection(
        (redis_url.hostname, redis_url.port),
        password=redis_url.password,
        loop=loop)
    print(foo)
    import types
    print(isinstance(foo, types.GeneratorType))
    conn = await foo
    print(conn)
    print('foo')
    import json
    foo = {'foo': 'bar'}
    #await conn.execute('set', 'my-key', json.dumps(foo))
    val = await conn.execute('get', 'my-key')
    print(json.loads(val))
    conn.close()
    await conn.wait_closed()


loop.run_until_complete(go())

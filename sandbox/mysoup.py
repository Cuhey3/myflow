from bs4 import BeautifulSoup
import aiohttp
import asyncio


async def foo():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://ameblo.jp/00dpd/') as resp:
            print(resp.status)
            soup = BeautifulSoup(await resp.text(), 'lxml')
            import re
            print(soup.find('a', class_='pagingNext'))
            for element in soup.find_all("img", src=re.compile("user_images")):
                print(element)


asyncio.get_event_loop().run_until_complete(foo())

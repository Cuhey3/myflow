import aiohttp
import asyncio
from aiohttp import web
from multidict import MultiDict


async def foo(request):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'http://www.rd.com/wp-content/uploads/sites/2/2016/04/01-cat-wants-to-tell-you-laptop.jpg'
        ) as resp:
            async with session.get(
                'https://cdn.kinsights.com/cache/2f/a0/2fa05bebbd843b9aa91e348a7e77d5c2.jpg'
            ) as resp2:
                boo = await resp.read()
                boo2 = await resp2.read()
                from zipfile import ZipFile
                import zipfile
                from io import BytesIO

                inMemoryOutputFile = BytesIO()

                zipFile = ZipFile(inMemoryOutputFile, 'w',
                                  zipfile.ZIP_DEFLATED)
                zipFile.writestr('OEBPS/content.jpg', boo)
                zipFile.writestr('OEBPS/content2.jpg', boo2)
                zipFile.close()
                print(zipFile)
                inMemoryOutputFile.seek(0)
                dir(inMemoryOutputFile)
                return web.Response(
                    headers=MultiDict({
                        'Content-Disposition':
                        'Attachment;filename=poyoyon.zip'
                    }),
                    body=inMemoryOutputFile)


'''
temporarylocation = "testout.zip"
with open(temporarylocation,
          'wb') as out:  ## Open temporary file as bytes
    out.write(inMemoryOutputFile.read())
'''
'''
            import gzip
            print(len(boo))
            data = gzip.compress(boo)
            print(len(data))
'''

app = web.Application()
app.router.add_get('/boo', foo)
web.run_app(app)

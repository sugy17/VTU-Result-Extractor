import asyncio
import ssl

headers = {}

ssl=ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

async def get_page(session, url, get_blob=False, chunksize=None):
    await asyncio.sleep(0.2)
    async with session.get(url, headers=headers,ssl=ssl) as resp:
        # print(resp.status)
        resp.raise_for_status()
        if chunksize:
            return await resp.content.read(chunksize)
        return await resp.read() if get_blob else await resp.text()


async def post_page(session, url, data):
    await asyncio.sleep(0.2)
    async with session.post(url, data=data, headers=headers, ssl=ssl) as resp:
        resp.raise_for_status()
        return await resp.text()
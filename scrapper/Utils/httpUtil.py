import asyncio


async def get_page(session, url, get_blob=False):
    await asyncio.sleep(0.2)
    async with session.get(url) as resp:
        # print(resp.status)
        resp.raise_for_status()
        return await resp.read() if get_blob else await resp.text()


async def post_page(session, url, data):
    await asyncio.sleep(0.2)
    async with session.post(url, data=data) as resp:
        resp.raise_for_status()
        return await resp.text()

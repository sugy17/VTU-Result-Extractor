import asyncio
from aiohttp import web

#web.static('/DATA', '.', show_index=True)

host = 'https://results.vtu.ac.in/'
db_url = "http://192.168.56.102:9000"


request_que = []
req_buffer = {}
current = []

my_loop = asyncio.get_event_loop()

app = web.Application()
# app.router.add_static('/static',
#                           path='./DATA',
#                           name='static')
#app.add_routes([web.static('/DATA', './DATA')])
entry_task = my_loop.create_task(asyncio.sleep(0.4))
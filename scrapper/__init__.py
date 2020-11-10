import asyncio
from aiohttp import web

host = 'https://results.vtu.ac.in/'
db_url = "https://semdata.rxav.pw/"


request_que = []
request_history = {}
current = []

my_loop = asyncio.get_event_loop()

app = web.Application()

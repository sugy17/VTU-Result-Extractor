from aiohttp.web import Application
from aiohttp_middlewares import cors_middleware


app = Application(middlewares=[cors_middleware(allow_all=True)])



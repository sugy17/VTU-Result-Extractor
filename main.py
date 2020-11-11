import os
import aiohttp
import aiohttp_cors
from aiohttp import web

from scrapper import deamon
from scrapper import app, my_loop
from scrapper.API.routes import get_req, send_stat,send_history ,index, usn_ui, send_res, reset, update_history
from scrapper.deamon import entry

try:
    os.mkdir('DATA')
    print('created DATA dir')
except:
    print('DATA dir present')

# Add endpoints
app.add_routes([web.get('/start', get_req),
                web.get('/status', send_stat),
                web.get('/reset', reset),
                web.get('/history', send_history),
                web.get('/update_history', update_history),
                web.static('/DATA', 'DATA', show_index=True),
                web.get('/', index),
                web.get('/usn', usn_ui),
                web.get('/individual', send_res)])

# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Configure CORS on all routes.
for route in list(app.router.routes()):
    cors.add(route)

runner = aiohttp.web.AppRunner(app)
my_loop.run_until_complete(runner.setup())
site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8000)
my_loop.run_until_complete(site.start())
deamon.entry_task = my_loop.create_task(entry())
my_loop.run_forever()

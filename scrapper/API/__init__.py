# import aiohttp
# import aiohttp_cors
# from aiohttp import web
# from scrapper import app, my_loop
# from .routes import get_req, send_stat, clear_queue
#
# # Add endpoints
# app.add_routes([web.get('/start', get_req),
#                 web.get('/status', send_stat),
#                 web.get('/clear_queue', clear_queue)])
#
# # Configure default CORS settings.
# cors = aiohttp_cors.setup(app, defaults={
#     "*": aiohttp_cors.ResourceOptions(
#         allow_credentials=True,
#         expose_headers="*",
#         allow_headers="*",
#     )
# })
#
# # Configure CORS on all routes.
# for route in list(app.router.routes()):
#     cors.add(route)
#
# runner = aiohttp.web.AppRunner(app)
# my_loop.run_until_complete(runner.setup())
# site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8000)
#
# print("Server started successfully")
#
# my_loop.run_until_complete(site.start())
from scrapper import my_loop
from scrapper.deamon import entry



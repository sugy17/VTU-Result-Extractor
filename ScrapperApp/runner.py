import os

os.makedirs(os.path.join("..", "data"), exist_ok=True)
os.makedirs(os.path.join("..", "data", "files"), exist_ok=True)

import asyncio
from aiohttp.web import run_app

from aiohttp_swagger import *

from Models.serverFunctions import init_db
from API import app, swagger
from API.routes import initialise_routes

from Scrapper import daemon

# todo add routes - EXAMS,URLs
# todo add USN check route


# Todo imp! fix make semstat-report unblocking

# todo check autocommit and autoflush
# todo aiohttp[speedups]
# todo migrate to aiosqlite
# todo standardise paths irrespective of current working dir


# initialise DB for request management
init_db()

# initialise interface (API) for app control and tracking requests
initialise_routes(app)
# initialise_routes(swagger)

# Run scrapper listener (Daemon)
my_loop = asyncio.get_event_loop()
app['entry_task'] = my_loop.create_task(daemon.entry(my_loop))
app['event_loop'] = my_loop

# Run Web-App on current event loop
setup_swagger(app, swagger_url='//',
              description="Main routes are /input/list , /history , /queue are fumctional and can be used for prototyping.Remaining routes are under development to satisfy non-functional requirements and QOL improvements.",
              title="Scrapper API",
              api_version="1.0.0",
              contact="sugy17cs@cmrit.ac.in")
run_app(app, port=8000)
import os

os.makedirs(os.path.join("..", "data"), exist_ok=True)
os.makedirs(os.path.join("..", "data", "files"), exist_ok=True)

import asyncio
from aiohttp.web import run_app

from aiohttp_swagger import *

from Models.models import init_db
from API import app
from API.routes import initialise_routes

from Scrapper import daemon


# todo add logger , remove prints
# todo add reval processing in semstat-report

# todo aiohttp[speedups]
# todo migrate to aiosqlite
# todo tests


# initialise DB for request management
init_db()

# initialise interface (API) for app control and tracking requests
initialise_routes(app)

# Run scrapper listener (Daemon)
my_loop = asyncio.get_event_loop()
app['entry_task'] = my_loop.create_task(daemon.entry(my_loop))
app['event_loop'] = my_loop

# setup swagger docs at '/info'
setup_swagger(app, swagger_url='/info',
              description='''Takes in url and list of USNS, scrapes for results from VTU's
                site and sweeps them into semstat-database for analysis.All routes are functional.
                Main route /input/list can be used for prototyping.Remaining
                routes are to fulfill non functional requirements and increase QOL''',
              title="Scrapper API",
              api_version="1.0.0",
              contact="sugy17cs@cmrit.ac.in")

# Run Web-App on current event loop
run_app(app, port=8440)

from aiohttp.web import Application
from aiohttp_middlewares import cors_middleware
from aiohttp_swagger3 import SwaggerDocs, SwaggerUiSettings

app = Application(middlewares=[cors_middleware(allow_all=True)])
swagger = SwaggerDocs(app, swagger_ui_settings=SwaggerUiSettings(path="/docs/"),
                      description="Main routes are /input/list and /queue.Can be used for prototyping.Remaining routes are under development and are for QOL improvements.",
                      title="Scrapper API",
                      version="1.0.0", )
app['storage'] = {}



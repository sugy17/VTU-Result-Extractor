from . import app
from Scrapper import daemon


def restart_deamon():
    app['entry_task'].cancel()
    app['entry_task'] = app['event_loop'].create_task(daemon.entry(app['event_loop']))

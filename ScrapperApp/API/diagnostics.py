from . import app
from Scrapper import daemon


def restart_deamon():
    # todo add change all request status to canceled if in precessing state
    # db_pre_restart()
    app['entry_task'].cancel()
    app['entry_task'] = app['event_loop'].create_task(daemon.entry(app['event_loop']))

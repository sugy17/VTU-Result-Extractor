from . import deamon
from . import my_loop


def restart_deamon():
    deamon.entry_task.cancel()
    deamon.entry_task = my_loop.create_task(deamon.entry())
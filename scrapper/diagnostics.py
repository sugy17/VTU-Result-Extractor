import scrapper
from scrapper.deamon import entry


def restart_deamon():
    scrapper.entry_task.cancel()
    scrapper.entry_task = scrapper.my_loop.create_task(entry())
import asyncio
from .Utils.exceptionHandler import handle_exception
from .handle import handle_list
from . import REQUEST_QUEUE


async def entry(event_loop):
    # await sync_subject_details()  -->  future devlopment
    while True:

        while len(REQUEST_QUEUE) == 0:
            # print(REQUEST_QUEUE)
            await asyncio.sleep(3)

        print("starting to process request")
        try:
            # progress is a db object containing progress(status) info of a request
            progress = REQUEST_QUEUE[0]
            await handle_list(event_loop, progress)
        except Exception as e:
            handle_exception(e,"notify")
        print("finished processing request")

        REQUEST_QUEUE.pop(0)

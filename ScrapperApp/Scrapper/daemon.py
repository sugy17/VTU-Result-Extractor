import asyncio
from .Utils.exceptionHandler import handle_exception
from .handle import handle_list
from . import REQUEST_QUEUE


async def entry(event_loop):
    # await sync_subject_details()  -->  future devlopment


    while True:
        try:
            while len(REQUEST_QUEUE) == 0:
                # print(REQUEST_QUEUE)
                await asyncio.sleep(3)

            # progress is a db object containing progress(status) info of a request
            progress = REQUEST_QUEUE[0]
            print("starting to process request: " + str(progress.id))
            try:
                await handle_list(event_loop, progress)
            except Exception as e:
                handle_exception(e, "notify")
            print("finished processing request: " + str(progress.id))

            REQUEST_QUEUE.pop(0)
        except Exception as e:
            handle_exception(e)
            REQUEST_QUEUE.clear()

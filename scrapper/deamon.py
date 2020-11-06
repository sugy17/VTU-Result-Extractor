import asyncio

from . import my_loop, req_buffer, current, request_que
from .Store.dataFiles import create_files
from .Utils.USN import usn_generator
from .Utils.exceptionHandler import handle_exception
from .dbClient import send_files_to_db
from .executer import async_executer
from .requestChronology import get_exam_name


entry_task = ''

async def entry():
    # global request_que, resultpage_url, indexpage_url, current, exam_name, resultpage_url

    invalid_count = 0
    # usn_gen = usn_generator(file_ = 'usns.txt')#clg_code='1cr', batches=['16'], depts=['ec'])
    files_structure = {}
    usns = []
    while True:
        current.clear()
        while len(request_que) == 0:
            # print(request_que)
            await asyncio.sleep(3)
        url, batch, dept, exam = request_que[0]
        current[:] = [url, batch, dept, exam]
        req_buffer[tuple(current)]['status'] = 'processing'
        indexpage_url = "/".join(url.split('/')[-2:])
        resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
        # print(indexpage_url,resultpage_url)
        try:
            while (True):
                await asyncio.sleep(3)
                try:
                    exam_name = await my_loop.create_task(get_exam_name(indexpage_url))
                    exam_name = exam_name.replace('/', '_')
                    break
                except Exception as e:
                    handle_exception(e)
            if exam_name != 'err' or len(exam_name) < 35:
                print('Sucess...Procceding')
                print(exam_name)
            else:
                print('Err in fetching index page...aborting')
                request_que[tuple(current)]['error'] = 'Err in fetching index page...aborting'
                continue
            usn_gen = usn_generator(clg_code='1cr', batches=[batch],
                                    depts=[dept], limit=2)
            while True:
                usns.clear()
                try:
                    if invalid_count > 10:
                        await create_files(files_structure, exam_name)
                        usns.append(usn_gen.send(True))
                    group_count = 0
                    while group_count < 3:
                        usns.append(next(usn_gen))
                        group_count += 1
                except Exception as e:
                    await my_loop.create_task(
                        async_executer(my_loop, invalid_count, usns, files_structure, indexpage_url, resultpage_url))
                    await create_files(files_structure, exam_name)
                    handle_exception(e, 'notify')
                    break
                invalid_count = await my_loop.create_task(
                    async_executer(my_loop, invalid_count, usns, files_structure, indexpage_url, resultpage_url))
            # send_files_to_db(exam_name)
            request_que.pop(0)
            req_buffer[tuple(current)]['status'] = 'complete'
        except Exception as e:
            handle_exception(e, 'notify')

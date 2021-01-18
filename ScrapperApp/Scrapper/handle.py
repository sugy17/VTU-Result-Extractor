import asyncio

from Models.models import session as localdb
from Models.crud import get_exam_id,check_usn

from .Store.dataFiles import create_files
from .Utils.USN import usn_inp
from .Utils.exceptionHandler import handle_exception
from .executer import batch_executer
from .requestChronology import get_exam_name  # , sync_subject_details

from .Store.Semester_Stats_Client import send_files_to_db


async def handle_list(event_loop, progress):
    files_structure = {}
    new_files = []
    usns = []
    url = progress.url.name
    indexpage_url = "/".join(url.split('/')[-2:])
    resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
    try:
        progress.status = 4
        localdb.commit()
        while True:
            await asyncio.sleep(3)
            try:
                exam_name = await event_loop.create_task(get_exam_name(indexpage_url))
                exam_name = exam_name.replace('/', '_')
                break
            except Exception as e:
                handle_exception(e)
        # exam_name = "debug"
        if exam_name != 0 and len(exam_name) < 35:
            print(exam_name)
            progress.exam_id = get_exam_id(exam_name)
        else:
            print('ERROR: Failed to get examination from VTU site...skiping request')
            progress.status = 0
            progress.description = 'ERROR: Failed to get examination from VTU site...skipped request'
            localdb.commit()
            return
        progress.status = 3
        localdb.commit()
        try:
            usn_gen = usn_inp(progress.inp)
        except Exception as e:
            progress.status = 9
            progress.description = 'ERROR:'+str(e)
            localdb.commit()
            return
        new_files.clear()
        while True:
            usns.clear()
            try:
                group_count = 0
                while group_count < 3:
                    usn = check_usn(next(usn_gen), progress.url_id, progress.exam_id,progress.update or progress.reval)
                    if not usn:
                        continue
                    usns.append(usn)
                    group_count += 1
            except Exception as e:
                await event_loop.create_task(
                    batch_executer(event_loop, usns, files_structure, indexpage_url, resultpage_url,
                                   localdb=localdb, progress=progress)
                )
                new_files.extend(await create_files(files_structure, exam_name))
                handle_exception(e, 'expected')
                break
            await event_loop.create_task(batch_executer(event_loop, usns, files_structure, indexpage_url, resultpage_url,
                                                        localdb=localdb, progress=progress))
        if len(new_files) == 0:
            progress.status = 1
            progress.description = 'no data generated'
            localdb.commit()
            return
        try:
            success = await send_files_to_db(exam_name, new_files)
            if not success:
                # await sync_subject_details()
                success = await send_files_to_db(exam_name, new_files)
                if not success:
                    raise Exception("something went wrong while sending to database")
        except Exception as e:
            handle_exception(e, 'notify')
            progress.description = 'ERROR: data not sent to semstats database'
            progress.status = 5
            return
        progress.status = 1
        localdb.commit()
    except Exception as e:
        progress.status = 0
        progress.description = 'Error: check logs.'
        handle_exception(e, 'notify')

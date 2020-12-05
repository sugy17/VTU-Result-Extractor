from .Parsers.HTMLParser import parse_resultpage
from .Store.Semester_Stats_Client import send_student_to_db
from .Store.dataFiles import populate_file_structure
from .Utils.exceptionHandler import handle_exception
from .requestChronology import get_resultpage


async def batch_executer(event_loop, invalid_count, usns, files_structure, indexpage_url, resultpage_url, localdb=None,
                         progress=None, save=True, ignore_invalid_count=False):
    tasks = []
    for usn in usns:
        tasks.append((event_loop.create_task(get_resultpage(usn.usn, indexpage_url, resultpage_url, save)), usn))
    for task, usn in tasks:
        resultpage = await task
        if resultpage == 8:
            invalid_count += ignore_invalid_count
            usn.status = 8
            localdb.commit()
            continue
        invalid_count = 0
        try:
            name, sems, result = parse_resultpage(resultpage)
        except Exception as e:
            handle_exception(e)
            print('error while processing:' + usn.usn)
            usn.status = 0
            localdb.commit()
            continue
        # print(usn + "  " + name)
        usn.status = 1
        progress.usn = usn.usn
        localdb.commit()
        populate_file_structure(files_structure, usn.usn, name, sems, result, save, progress.id)
    return invalid_count


async def async_executer(usn, files_structure, indexpage_url, resultpage_url, localdb=None, save=True):
    resultpage = await get_resultpage(usn.usn, indexpage_url, resultpage_url, save)
    if resultpage == 8:
        usn.status = 8
        localdb.commit()
    try:
        name, sems, result = parse_resultpage(resultpage)
    except Exception as e:
        handle_exception(e)
        print('error while processing:' + usn.usn)
        usn.status = 0
        localdb.commit()
        return [str(e)]  # ["Unable to connect to vtu site"]
    data = populate_file_structure(files_structure, usn.usn, name, sems, result, save)
    return data

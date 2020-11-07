from .HTMLParser.pageParser import parse_resultpage
from .Store.dataFiles import populate_file_structure
from .requestChronology import get_resultpage
from .Utils.exceptionHandler import handle_exception
from . import req_buffer, current


async def async_executer(event_loop, invalid_count, usns, files_structure, indexpage_url, resultpage_url, save=True):
    tasks = []
    for usn in usns:
        tasks.append((event_loop.create_task(get_resultpage(usn, indexpage_url, resultpage_url)), usn))
    for task, usn in tasks:
        resultpage = await task
        if resultpage == "invalid":
            invalid_count += 1
            continue
        invalid_count = 0
        try:
            name, sems, result = parse_resultpage(resultpage)
        except Exception as e:
            handle_exception(e)
            print('error while processing:' + usn)
            continue
        # print(usn + "  " + name)
        if save:
            req_buffer[tuple(current)]['usn'] = usn
            populate_file_structure(files_structure, usn, name, sems, result)
        else:
            return populate_file_structure(files_structure, usn, name, sems, result, save)
    return invalid_count

import re
import os
import aiofiles
from ..Utils.exceptionHandler import handle_exception


def populate_file_structure(files_structure, usn, name, sems, result, save=True, rid=0):
    send_res = []
    for j in range(0, len(sems)):
        sem = sems[j]
        dept = re.findall(r'[0-9]([a-z]{2}|[a-z]{3}])[0-9]*?', usn)[1]
        batch = '20' + re.findall(r'[a-z]([0-9][0-9])[a-z]', usn)[0]
        rows = result[j].find_all('div', {'class': 'divTableRow'})[1:]
        dip = '-dip' if int(re.findall(r'[0-9]{3}', usn)[0]) >= 400 else ''
        scheme = '20' + rows[0].text.strip().replace(',', '').split('\n')[0][0:2]
        file = 'Data-' + dept.upper() + '-' + batch + '-' + scheme + '-' + sem + (
            '-arrear' if j != 0 else '') + dip + '-Req_' + str(rid) + '.csv'
        if file not in files_structure:
            files_structure[file] = []
        files_structure[file].append([usn, name, sem])
        for row in rows:
            for sub in row.find_all('div', {'class': 'divTableCell'}):
                files_structure[file][-1].append(sub.text.strip().replace(',', '').replace('\t', ''))
        if not save:
            send_res.append(files_structure[file][-1])
    if not save:
        # print(*files_structure[file][-1], sep=',')   ## debug
        return send_res


async def create_files(files_structure, dir_name):
    try:
        try:
            dir_name = os.path.join('..', 'data', 'files', dir_name)
            os.mkdir(dir_name)
        except Exception as e:
            handle_exception(e, "expected")
            print(dir_name + ' arlready exists')
        for file in files_structure:
            fp = await aiofiles.open(os.path.join(dir_name, file), mode='w')
            for record in files_structure[file]:
                await fp.write(str(record).replace('[', '').replace('\'', '').replace(', ', ',').replace(']', ',\n'))
            await fp.close()
        print(files_structure)
    except Exception as e:
        handle_exception(e)
    new_files = list(files_structure.keys())
    files_structure.clear()
    return new_files

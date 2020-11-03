import re
import os
import aiofiles
from ..Utils.exceptionHandler import handle_exception


def populate_file_structure(files_structure, usn, name, sems, result):
    for j in range(0, len(sems)):
        sem = sems[j]
        dept = re.findall(r'[0-9]([a-z]{2}|[a-z]{3}])[0-9]*?', usn)[1]
        batch = '20' + re.findall(r'[a-z]([0-9][0-9])[a-z]', usn)[0]
        rows = result[j].find_all('div', {'class': 'divTableRow'})[1:]
        scheme = '20' + rows[0].text.strip().replace(',', '').split('\n')[0][0:2]
        file = 'Data-' + dept.upper() + '-' + batch + '-' + scheme + '-' + sem + ('-arrear' if j != 0 else '') + '.csv'
        if file not in files_structure:
            files_structure[file] = []
        files_structure[file].append([usn, name, sem])
        # temp.append([usn,name,sems[j]])
        for row in rows:
            for sub in row.find_all('div', {'class': 'divTableCell'}):
                files_structure[file][-1].append(sub.text.strip().replace(',', '').replace('\t', ''))
        # for row in rows:
        #     files_structure[file][-1].extend(row.text.strip().replace(',', '').split('\n'))
        print(*files_structure[file][-1], sep=',')


async def create_files(files_structure, dir_name):
    try:
        try:
            dir_name = os.path.join('DATA/', dir_name)
            os.mkdir(dir_name)
        # except Exception as e:
        #     handle_exception(e,"expected")
        #     dir_name = dir_name + '_updated'
        #     try:
        #         os.mkdir(dir_name)
        except Exception as e:
            handle_exception(e, "expected")
            print(dir_name + ' arlready exists')
        for file in files_structure:
            fp = await aiofiles.open(os.path.join(dir_name, file), mode='w')
            for record in files_structure[file]:
                await fp.write(str(record).replace('[', '').replace('\'', '').replace(', ', ',').replace(']', ',\n'))
            await fp.close()
    except Exception as e:
        handle_exception(e)
    print(files_structure)
    files_structure.clear()

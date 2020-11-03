import random
import sys
import asyncio
import re
import os
import io
import requests as req
import aiohttp
import aiofiles
import numpy
from bs4 import BeautifulSoup as bs
import pytesseract
from PIL import Image as pimg
from wand.image import Image as wimg
from semester_stats_report import ScoreReport, StudentReport, SubjectReport
from semester_stats_report import SemesterClient
import csv
from typing import Set
from aiohttp import web
import aiohttp_cors

currentdir = os.path.join(os.getcwd(),'/')

host = 'https://results.vtu.ac.in/'
# host='https://210.212.207.149:443/'

request_que = []
req_buffer = {}
current = []
resultpage_url = 'AS_CBCS/resultpage.php'
indexpage_url = 'AS_CBCS/index.php'
req.packages.urllib3.disable_warnings()
sem_regx = re.compile('Semester')
exam_name_regx = re.compile('<b>.*>(.*?) EXAMINATION RESULTS')  ##improve
catch_alert_regx = re.compile(r'alert\((.*)\)')


def handle_exception(e, risk='notify'):
    if risk == 'notify':
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(fname, exc_tb.tb_lineno, exc_type, e)
    pass


async def read_captcha(captcha_blob):
    pic = wimg(blob=captcha_blob)
    pic.modulate(120)
    pic.modulate(150)
    pic.modulate(130)
    # pic.save(filename='pic.png')
    img_buffer = numpy.asarray(bytearray(pic.make_blob(format='png')), dtype='uint8')
    bytesio = io.BytesIO(img_buffer)
    pil_img = pimg.open(bytesio)
    return re.sub('[\W_]+', '', pytesseract.image_to_string(pil_img))


async def get_page(session, url, get_blob=False):
    await asyncio.sleep(0.2)
    async with session.get(url) as resp:
        # print(resp.status)
        resp.raise_for_status()
        return await resp.read() if get_blob else await resp.text()


async def post_page(session, url, data):
    await asyncio.sleep(0.2)
    async with session.post(url, data=data) as resp:
        resp.raise_for_status()
        return await resp.text()


async def get_resultpage(usn):
    # global ccount
    retry_count = 0
    # cookie = {'PHPSESSID': 'q6k5bedrobcjob6opttgg11i14'+str(ccount)}
    while True:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ttl_dns_cache=500, ssl=False)) as session:
                index_page, img_src, token, captcha_blob, captcha_code = "", "", "", "", ""
                try:
                    index_page = await get_page(session, host + indexpage_url)
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(0, 3))
                    continue
                if len(index_page) < 5000:
                    retry_count += 1
                    if retry_count > 4:
                        return None  # return meaning full error codes or throw exception
                    continue
                try:
                    img_src, token = parse_indexpage(index_page)
                    captcha_blob = await get_page(session, host + img_src, True)
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(0, 3))
                    continue
                if len(captcha_blob) < 1000:
                    continue
                try:
                    captcha_code = await read_captcha(captcha_blob)  ##cpu blocking
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(0, 3))
                    continue
                # print(captcha_code)
                if len(captcha_code) != 6:
                    continue
                data = {'Token': token, 'lns': usn, 'captchacode': captcha_code}
                resultpage = ""
                try:
                    resultpage = await post_page(session, host + resultpage_url, data)
                except Exception as e:
                    handle_exception(e)
                    await asyncio.sleep(random.uniform(3, 6))
                    continue
                # if len(resultpage) < 1000:  #optimise alert decetion
                try:
                    alert = catch_alert_regx.findall(resultpage)[0]
                    if 'captch' in alert:
                        continue
                    elif 'not available' in alert:
                        print(usn, alert)
                        return "invalid"
                    elif 'check' in alert or 'after' in alert or 'again' in alert:
                        # print(usn, alert)
                        await asyncio.sleep(random.uniform(0, 3))
                        continue
                    # print(usn, alert)
                    # return meaning full err data
                except Exception as e:
                    handle_exception(e, 'expected')
                    pass
                return resultpage
        except Exception as e:
            handle_exception(e)
            pass


def parse_indexpage(page):
    soup = bs(page, 'html.parser')
    img_src = soup.find(alt="CAPTCHA code")['src']
    token = soup.find('input')['value']
    return img_src, token


def parse_resultpage(page):
    soup = bs(page, 'html.parser')
    # print(soup.find_all('div',{'class':'divTableCell'}))
    name = soup.find('table').find_all('tr')[1].find_all('td')[1].text[2:]
    sems = [list(i for i in e.split() if i.isdigit())[0] for e in
            soup(text=sem_regx)]  # sems=[ e[11] for e in soup(text=sem_regx)]
    result = soup.find_all('div', {'class': 'divTableBody'})
    return name, sems, result


async def get_exam_name():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ttl_dns_cache=500, ssl=False)) as  session:
        index_page = await get_page(session, host + indexpage_url)
        if len(index_page) < 5000:
            return 'err'
        return exam_name_regx.findall(index_page, re.DOTALL)[0]


def usn_generator(clg_code='1cr', batches=['16'], depts=['cs', 'ec'], file_=None):
    # global clg_code,batch,depts,dept_over
    if not file_:
        for dept in depts:
            for batch in batches:
                for number in range(1, 2):
                    change_section = yield clg_code + batch + dept + str(number).zfill(3)
                    if change_section is True:
                        break
                dip = batch[0] + str(int(batch[1]) + 1)  # change
                for number in range(400, 401):
                    change_section = yield clg_code + dip + dept + str(number).zfill(3)
                    if change_section is True:
                        break
    else:
        try:
            fh = open(file_, 'r')
            res = fh.readline()
            while (res != ''):
                yield res.strip().lower()
                res = fh.readline()
            raise Exception('Done reading file')
        except:
            raise Exception('error reading from file!!')


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
        pass
    print(files_structure)
    files_structure.clear()


async def async_executer(event_loop, invalid_count, usns, files_structure):
    global current, req_buffer
    tasks = []
    for usn in usns:
        tasks.append((event_loop.create_task(get_resultpage(usn)), usn))
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
        req_buffer[tuple(current)]['usn'] = usn
        populate_file_structure(files_structure, usn, name, sems, result)
    return invalid_count

def chunk(lst, n):
    # Helper Function for The Code Below
    # This just Splits up the Below into sublists.
    for i in range(0, len(lst), n):
        yield lst[i : i + n]

async def entry():
    global request_que, resultpage_url, indexpage_url, current

    # This is the Main Client, Use it to POST data.
    cl = SemesterClient("http://192.168.56.102:9000")
    # We are keeping Sets to Avoid Duplication.
    stu_keep: Set[StudentReport] = set()
    sub_keep: Set[SubjectReport] = set()
    sco_keep: Set[ScoreReport] = set()

    invalid_count = 0
    # usn_gen = usn_generator(file_ = 'usns.txt')#clg_code='1cr', batches=['16'], depts=['ec'])
    files_structure = {}
    usns = []
    while True:
        current.clear()
        while len(request_que) == 0:
            #print(request_que)
            await asyncio.sleep(3)
        url, batch, dept, exam = request_que[0]
        current[:] = [url, batch, dept, exam]
        req_buffer[tuple(current)]['status'] = 'processing'
        indexpage_url = "/".join(url.split('/')[-2:])
        resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
        try:
            while (True):
                await asyncio.sleep(3)
                try:
                    exam_name = await my_loop.create_task(get_exam_name())
                    exam_name = exam_name.replace('/', '_')
                    break
                except Exception as e:
                    handle_exception(e)
                    pass
            if exam_name != 'err' or len(exam_name) < 35:
                print('Sucess...Procceding')
                print(exam_name)
            else:
                print('Err in fetching index page...aborting')
                request_que[tuple(current)]['error'] = 'Err in fetching index page...aborting'
                continue
            usn_gen = usn_generator(clg_code='1cr', batches=[batch],
                                    depts=[dept])
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
                    await my_loop.create_task(async_executer(my_loop, invalid_count, usns, files_structure))
                    await create_files(files_structure, exam_name)
                    handle_exception(e, 'notify')
                    break
                invalid_count = await my_loop.create_task(async_executer(my_loop, invalid_count, usns, files_structure))
            for f_name in os.listdir(os.path.join('DATA', exam_name)):
                with open(os.path.join('DATA', exam_name, f_name)) as f:
                    _data = csv.reader(f.readlines(), delimiter=",")
                    # For Each Row:

                    for x in _data:
                        x = x[: len(x) - 2]
                        # Create Student
                        stu_keep.add(StudentReport(Name=x[1], Usn=x[0]))
                        for y in chunk(x[3:], 6):
                            # Subject And Score for Each.
                            sub_keep.add(
                                SubjectReport(
                                    Code=y[0],
                                    Name=y[1],
                                    MinExt=19,
                                    MinTotal=40,
                                    MaxTotal=100,
                                    Credits=4,
                                )
                            )
                            sco_keep.add(
                                ScoreReport(Usn=x[0], SubjectCode=y[0], Internals=y[2], Externals=y[3])
                            )

                # Data is scrubbed!
                # Send the StudentReports First
                cl.bulk().student(list(stu_keep))
                # Send Subject Reports Second.
                cl.bulk().subject(list(sub_keep))
                # Send the Score Reports AT THE LAST:
                cl.bulk().scores(list(sco_keep))

                stu_keep.clear()
                sub_keep.clear()
                sco_keep.clear()
            request_que.pop(0)
            req_buffer[tuple(current)]['status'] = 'complete'
        except Exception as e:
            handle_exception(e, 'notify')
            pass


# Setting up endpoints
routes = web.RouteTableDef()


@routes.get("/status")
async def send_stat(request):
    global req_buffer, current
    try:
        # url = request.rel_url.query.get('url')
        # batch = request.rel_url.query.get('batch')
        # dept = request.rel_url.query.get('dept')
        # exam = request.rel_url.query.get('exam')
        # req_buffer[(url, batch, dept, exam)]['queue'] = [i[1] + i[2] for i in request_que]
        if len(current) != 0:
            req_buffer[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
            return web.json_response(req_buffer[tuple(current)])
        else:
            return web.json_response({"queue":"No jobs in queue"})
    except Exception as e:
        return web.json_response([str(e)])


@routes.get("/start")
async def get_req(request):
    global req_buffer, request_que, current
    try:
        url = request.rel_url.query.get('url')
        batch = request.rel_url.query.get('batch')
        dept = request.rel_url.query.get('dept')
        exam = request.rel_url.query.get('exam')
        if (url, batch, dept, exam) not in req_buffer or req_buffer[(url, batch, dept, exam)]['status'] == 'error':
            request_que.append((url, batch, dept, exam))
            req_buffer[(url, batch, dept, exam)] = {'usn': '-','status':'added' }
        if len(current) == 0:
            current[:] = [url, batch, dept, exam]
        req_buffer[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
        return web.json_response(req_buffer[tuple(current)])
    except Exception as e:
        return web.json_response({'msg': 'error'})

@routes.get("/clear_queue")
async def clear_queue(request):
    global request_que, entry_task
    try:
        entry_task.cancel()
        for i in request_que:
            del(req_buffer[i])
        request_que.clear()
        entry_task = my_loop.create_task(entry())
        return web.json_response({"msg":"cleared_queue"})
    except Exception as e:
        return web.json_response({'msg': 'error'})


my_loop = asyncio.get_event_loop()
app = web.Application()

# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

app.add_routes(routes)
# Configure CORS on all routes.
for route in list(app.router.routes()):
    cors.add(route)

runner = aiohttp.web.AppRunner(app)
my_loop.run_until_complete(runner.setup())
site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8000)
my_loop.run_until_complete(site.start())
entry_task = my_loop.create_task(entry())
my_loop.run_forever()

import os

import aiohttp
from aiohttp import web
from aiohttp.web_routedef import post, delete
from aiohttp.web import get, static

from Models.models import Progress, session as localdb
from Models.crud import get_url_id, get_exam_id, check_usn, get_exams, get_urls, query_usn_data, query_exam_name
from Scrapper import REQUEST_QUEUE
from Scrapper.executer import async_executer
from Scrapper.Utils.exceptionHandler import handle_exception
from Scrapper.requestChronology import get_exam_name
from Scrapper.Store.Semester_Stats_Client import send_student_to_db
from Scrapper.Parsers.HTMLParser import parse_for_links
from Scrapper.Utils.httpUtil import get_page

from .diagnostics import restart_deamon


async def single_usn(request):
    """
    ---
    description: (Primarily for testing and helper for internal UI) This end-point takes in a single USN along with source URL.Response time for this route may be more than 5 seconds..
    tags:
    - INPUT
    parameters:
    - in: query
      name: url
      description: Link of VTU Index page (spcifically the page where usn is given).
      type: string
      required: true
    - in: query
      name: usn
      description: 10 lettered string.
      type: string
      required: true
    - in: query
      description: Flag to indicate reval result or main result
      required: true
      name: reval
      type: boolean
    responses:
        "200":
            description: successful operation. Returns a json with result of usn.
        "405":
            description: invalid HTTP Method
    """
    try:
        usn = request.rel_url.query.get('usn').lower()
        url = request.rel_url.query.get('url')
        reval = request.rel_url.query.get('reval') in ["True", "true"]
        force = True
        # try: todo #design
        #     force = request.rel_url.query.get('force') in ['true','True']
        # except:
        #     force = True
        indexpage_url = "/".join(url.split('/')[-2:])
        resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
        print(request.rel_url)
        if len(usn) != 10:
            return web.json_response({'data': ["invalid usn"]})
        url_id = get_url_id(url)
        i = 0
        while True:
            try:
                exam = await get_exam_name(indexpage_url)
            except Exception as e:
                handle_exception(e)
                exam = 0
            if exam != 0:
                if len(exam) < 35 or force:
                    break
                else:
                    # todo #desgin
                    return web.json_response({'data': [
                        "is this the right exam name displayed on site? Yes No'" + exam + "' if not contact admin."]})
            elif i > 3:
                return web.json_response({'data': ["VTU site is down"]})
            i += 1
        exam = exam.replace('/', '_')
        exam_id = get_exam_id(exam)
        usn_obj = check_usn(usn, url_id, exam_id, force=True)
        data = await async_executer(usn_obj, {}, indexpage_url, resultpage_url, localdb=localdb, save=False,
                                    reval=reval)
        print(data)
        sent = await send_student_to_db(data, reval)
        if not sent:
            print("something went wrong while sending to databse")
            usn_obj.status = 5
            localdb.commit()
        else:
            usn_obj.status = 1
            localdb.commit()
        return web.json_response({'data': data})
    except Exception as e:
        return web.json_response({'data': ['ERROR:' + str(e)]})


# add list usn input route
async def list_inp(request):
    """
    ---
    description: This end-point takes a list of USNs along with source URL and reval(=true or false).
    tags:
    - INPUT
    parameters:
    - in: query
      name: url
      description: Link of VTU Index page (spcifically the page where usn is given).
      type: string
      required: true
    - in: query
      description: Indicate whether reval or not
      required: true
      name: reval
      type: boolean
    - in: body
      name: inp
      description: String of comma separated usns or usn ranges.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns queue containing a list of queued requests(objects).
            schema:
                type: object
                properties:
                    queue:
                        type: array
                        items: object
        "405":
            description: invalid HTTP Method
    """
    try:
        data = await request.json()
    except Exception as e:
        handle_exception(e, risk="ok")
        data = await request.post()

    if len(data['usns']) < 10:
        return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})

    url = request.rel_url.query.get('url')
    reval = request.rel_url.query.get('reval') in ['True', 'true']
    progress = Progress(inp=data['usns'], reval=reval)
    progress.url_id = get_url_id(url)
    localdb.add(progress)
    localdb.commit()
    REQUEST_QUEUE.append(progress)
    return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})


async def queue_get(request) -> web.json_response:
    """
    ---
    description: This end-point returns list of queued up request objects.
    tags:
    - REQUEST QUEUE
    responses:
        "200":
            description: successful operation. Returns queue containing a list of request objects.
            schema:
                type: object
                properties:
                    queue:
                        type: array
                        items: object
    """
    return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})


async def queue_cancel(request) -> web.json_response:
    """
    ---
    description: Use to cancel a request.
    tags:
    - REQUEST QUEUE
    parameters:
    - in: path
      name: request_id
      description: request id of request object.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns queue.
            schema:
                type: object
                properties:
                    queue:
                        type: array
                        items: object
        "404":
            description: Request not found.
        "405":
            description: invalid HTTP Method
    """
    request_id = request.match_info['request_id']
    try:
        for i in range(len(REQUEST_QUEUE)):
            if str(REQUEST_QUEUE[i].id) == request_id:
                REQUEST_QUEUE[i].status = 7
                localdb.commit()
                del (REQUEST_QUEUE[i])
                if i == 0:
                    restart_deamon()
                return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})
        return web.json_response({"error": "request object not found in queue"}, status=404)
    except Exception as e:
        localdb.rollback()
        return web.json_response({"error": str(e)})


async def history_get(request):
    """
    ---
    description: This end-point returns a list of past requests.
    tags:
    - HISTORY
    responses:
        "200":
            description: successful operation. Returns history records along with queue
        "405":
            description: invalid HTTP Method
    """
    return web.json_response({
        'records': [progress.to_json() for progress in localdb.query(Progress)],
        'queue': [progress.to_json() for progress in REQUEST_QUEUE]
    }, status=200)


async def history_instance_get(request):
    """
    ---
    description: This end-point returns info on a specfic request.
    tags:
    - HISTORY
    parameters:
    - in: path
      name: request_id
      description: request id of request object.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns json containing info.
        "404":
            description: Request not found.
        "405":
            description: invalid HTTP Method
    """
    request_id = request.match_info['request_id']
    progress = localdb.query(Progress).filter(Progress.id == request_id).first()
    if not progress:
        return web.json_response({'error': 'ERROR:404'}, status=404)
    return web.json_response(progress.to_json(), status=200)


async def history_instance_delete(request):
    """
    ---
    description: This end-point deletes a request info (used in case it causes problems to initiate new requests).
    tags:
    - HISTORY
    parameters:
    - in: path
      name: request_id
      description: request id of request object.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns json containing info of deleted request details.
        "405":
            description: invalid HTTP Method
    """
    request_id = request.match_info['request_id']
    progress = localdb.query(Progress).filter(Progress.id == request_id).first()
    if not progress:
        return web.json_response({"error": "instance not found"}, status=404)
    try:
        for i in range(len(REQUEST_QUEUE)):
            if str(REQUEST_QUEUE[i].id) == request_id:
                del (REQUEST_QUEUE[i])
                if i == 0:
                    restart_deamon()
        localdb.delete(progress)
        localdb.commit()
    except Exception as e:
        localdb.rollback()
        return web.json_response({"error": str(e)})
    return web.json_response(progress.to_json())


async def files_get(request):
    """
    ---
    description: This end-point fetches links to all files generated for a particular exam.
    tags:
    - DATA
    parameters:
    - in: path
      name: exam_id
      description: row id of the exam in db.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns json .
        "405":
            description: invalid HTTP Method
    """
    exam_id = request.match_info['exam_id']
    try:
        exam = query_exam_name(exam_id)
    except Exception as e:
        return web.json_response({"error": ["ERROR:" + str(e)]}, status=404)
    return web.json_response(os.listdir(os.path.join('..', 'data', 'files', exam)))


async def send_file(request):
    """
    ---
    description: This end-point fetches a csv file of a particular exam.
    tags:
    - DATA
    parameters:
    - in: path
      name: name
      description: The file name.
      type: string
      required: true
    - in: path
      name: exam_id
      description: The file name.
      type: string
      required: true
    responses:
        "200":
            description: successful operation. Returns json .
        "405":
            description: invalid HTTP Method
    """
    f_name = request.match_info['name']
    exam_id = request.match_info['exam_id']
    try:
        exam = query_exam_name(exam_id)
        return web.FileResponse(os.path.join('..', 'data', 'files', exam, f_name))
    except Exception as e:
        return web.json_response({"error": "ERROR:" + str(e)})


async def url_get(request):
    """
    ---
    description: This end-point  fetches all urls from where data is scrapped along with url_id.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation. Returns json .
        "405":
            description: invalid HTTP Method
    """
    return web.json_response(get_urls())


async def exam_get(request):
    """
    ---
    description: This end-point  fetches all exams from where data is scrapped along with exam_id.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    return web.json_response(get_exams())


async def usn_get(request):
    """
    ---
    description: This end-point fetches all usn records with the specified  url_id and exam_id. **Note** - If no url_id is specified there will be multiple records with the same usn.
    tags:
    - DATA
    parameters:
    - in: path
      name: exam_id
      description: exam id of the exam in db.
      type: string
      required: true
    - in: query
      name: url_id
      description: url id of the url in db.
      type: string
      required: false
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    try:
        exam_id = request.match_info['exam_id']
        try:
            url_id = request.rel_url.query.get('url_id')
        except:
            url_id = None
        return web.json_response(query_usn_data(url_id, exam_id))
    except:
        return web.json_response({"error": "ERROR:Not found"}, status=404)


async def usn_instance_get(request):
    """
    ---
    description: This end-point fetches info of particular usn, used to check if usn is scrapped from a particlar url if url_id is specified along with exam_id, else returns usn along with all urls as separate records.
    tags:
    - DATA
    parameters:
    - in: path
      name: exam_id
      description: exam id of the exam in db.
      type: string
      required: true
    - in: path
      name: usn
      description: usn of student.
      type: string
      required: true
    - in: query
      name: url_id
      description: url id of the url in db.
      type: string
      required: false
    responses:
        "200":
            description: successful operation. Returns json .
        "404":
            description: usn is not scrapped.
        "405":
            description: invalid HTTP Method
    """
    exam_id = request.match_info['exam_id']
    usn = request.match_info['usn'].lower()
    try:
        url_id = request.rel_url.query.get('url_id')
    except:
        url_id = None
    try:
        return web.json_response(query_usn_data(url_id, exam_id, usn))
    except:
        return web.json_response({"error": "ERROR:Not found"}, status=404)


# static helpers
async def favicon(request):
    print('favicon.ico')
    return web.FileResponse(os.path.join('..', 'default_ui', 'favicon.ico'))


async def usn_ui(request):
    """
    ---
    description: This end-point returns a page which takes in a single USN along with source URL (part of internal UI).
    tags:
    - DEFAULT UI
    responses:
        "200":
            description: successful operation. Returns a static page.
        "405":
            description: invalid HTTP Method
    """
    print('usn_ui.html')
    return web.FileResponse(os.path.join('..', 'default_ui', 'usn.html'))


async def list_ui(request):
    """
    ---
    description: This end-point returns a page which takes in a list of USNs along with source URL (part of internal UI).
    tags:
    - DEFAULT UI
    responses:
        "200":
            description: successful operation. Returns a static page.
        "405":
            description: invalid HTTP Method
    """
    print('list.html')
    return web.FileResponse(os.path.join('..', 'default_ui', 'list.html'))

async def root(request):
    # Same as list_ui, written this way to not appear in swagger info
    print('list.html')
    return web.FileResponse(os.path.join('..', 'default_ui', 'list.html'))

async def get_links(request):
    """
    ---
    description: This end-point returns a list of urls (helper for get internal UI).
    tags:
    - DATA
    responses:
        "200":
            description: successful operation. Return urls.
        "405":
            description: invalid HTTP Method
    """
    try:
        async with aiohttp.ClientSession() as session:
            vtu_page = await get_page(session, 'https://results.vtu.ac.in')
        if len(vtu_page) < 5000:
            return web.json_response({'message':'COULDNT CONNECT TO VTU. Try again later'})
        res = await parse_for_links('https://results.vtu.ac.in',vtu_page, "hello")
        return web.json_response(res)
    except Exception as e:
        return web.json_response({'message':'COULDNT CONNECT TO VTU. Try again later'})
    

# initialisation helper
def initialise_routes(app):
    app.add_routes(
        [
            static('/DATA', os.path.join('..', 'data', 'files'), show_index=True),
            get('/ui/favicon.ico', favicon, allow_head=False),
            get('/ui/test', usn_ui, allow_head=False),
            get('/input/usn', single_usn, allow_head=False),
            get('/ui/list', list_ui, allow_head=False),
            get('/', root, allow_head=False),
            post('/input/list', list_inp),
            get('/queue', queue_get, allow_head=False),
            delete('/queue/{request_id}', queue_cancel),
            get('/history', history_get, allow_head=False),
            get('/history/{request_id}', history_instance_get, allow_head=False),
            delete('/history/{request_id}', history_instance_delete),
            get('/data/url', url_get, allow_head=False),
            get('/data/exam', exam_get, allow_head=False),
            get('/data/exam/{exam_id}/file', files_get, allow_head=False),
            get('/data/exam/{exam_id}/file/{file_name}', send_file, allow_head=False),
            get('/data/exam/{exam_id}/usn', usn_get, allow_head=False),
            get('/data/exam/{exam_id}/usn/{usn}', usn_instance_get, allow_head=False),
            get('/data/vtu_links', get_links, allow_head=False),
        ]
    )
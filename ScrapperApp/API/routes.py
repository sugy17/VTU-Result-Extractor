import os
from aiohttp import web
from aiohttp.web_routedef import post, delete
from aiohttp.web import get, static

from Models.models import Progress, session as localdb
from Models.serverFunctions import get_url_id, get_exam_id, check_usn
from Scrapper import REQUEST_QUEUE
from Scrapper.executer import async_executer
from Scrapper.Utils.exceptionHandler import handle_exception
from Scrapper.requestChronology import get_exam_name

from .diagnostics import restart_deamon

__version__ = '0.1.0'


# todo change according to executer chnages
async def single_usn(request):
    """
    ---
    description: (Primarily for testing and helper for internal UI) This end-point takes in a single USN along with source URL.Response time for this route may be more than 5 seconds..
    tags:
    - INPUT
    responses:
        "200":
            description: successful operation. Returns a json with result of usn.
        "405":
            description: invalid HTTP Method
    """
    try:
        usn = request.rel_url.query.get('usn').lower()
        url = request.rel_url.query.get('url')
        try:
            force = bool(request.rel_url.query.get('force'))
        except:
            force = False
        indexpage_url = "/".join(url.split('/')[-2:])
        resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
        print(request.rel_url)
        if len(usn) != 10:
            return web.json_response(["invalid usn"])
        url_id = get_url_id(url)
        i = 0
        while True:
            exam = await get_exam_name(indexpage_url)
            if exam != 0:
                if len(exam) < 35 or force:
                    break
                else:
                    return web.json_response({'data': [
                        "is this the right exam name displayed on site? Yes No'" + exam + "' if not contact admin."]})
            elif i > 3:
                return web.json_response({'data': ["VTU site is down"]})
            i += 1
        exam_id = get_exam_id(exam)
        usn_obj = check_usn(usn, url_id, exam_id, force=True)
        return web.json_response(
            {'data': await async_executer(usn_obj, {}, indexpage_url, resultpage_url, localdb=localdb, save=False)})
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
    - in: body
      name: url
      description: Link of VTU Index page (spcifically the page where usn is given).
      type: string
      required: true
    - in: body
      name: inp
      description: String of comma separated usns or usn ranges.
      type: string
      required: true
    - in: body
      description: Indicate whether reval or not
      required: true
      name: reval
      type: boolean
    responses:
        "200":
            description: successful operation. Returns queue containing a list of objects.
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

    if len(data['usns'])<10:
        return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})

    progress = Progress(rtype=1, inp=data['usns'], reval=data['reval'])
    progress.url_id = get_url_id(data['url'])
    localdb.add(progress)
    localdb.commit()
    REQUEST_QUEUE.append(progress)
    return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE]})


# async def batch_inp(request):
#     # """
#     # ---
#     # description: This end-point accept batch and dept along with url and queues the request.
#     # tags:
#     # - INPUT
#
#
#     # responses:
#     #     "200":
#     #         description: successful operation. Returns queue and progress
#     #     "405":
#     #         description: invalid HTTP Method
#     # """
#     data = await request.json()
#     progress = Progress(batch=data['batch'], dept=data['dept'], rtype=0)
#     progress.url_id = get_url_id(data['url'])
#     flag = True
#     for i in REQUEST_QUEUE:
#         if i.url == data['url'] and i.batch == data['batch'] and i.dept == data['dept']:
#             flag = False
#             break
#     if flag:
#         localdb.add(progress)
#         localdb.commit()
#         REQUEST_QUEUE.append(progress)
#     return web.json_response(
#         {
#             'queue': [progress.to_json() for progress in REQUEST_QUEUE]
#         },
#         status=200
#     )


async def queue_get(request) -> web.json_response:
    """
    ---
    description: This end-point returns queued up request.
    tags:
    - REQUEST QUEUE
    responses:
        "200":
            description: successful operation. Returns queue containing a list of objects.
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
    description: This end-point is cancels a request.
    tags:
    - REQUEST QUEUE
    responses:
        "200":
            description: successful operation. Returns queue and success message.
        "405":
            description: invalid HTTP Method
    """
    request_id = request.match_info['request_id']
    try:
        for i in REQUEST_QUEUE:
            if i.id == request_id:
                i.status = 7
            del (REQUEST_QUEUE[0])
            localdb.commit()
            restart_deamon()
            return web.json_response({'queue': [progress.to_json() for progress in REQUEST_QUEUE], 'msg': 'success'})
        return web.json_response({"error": "request object not found"}, status=404)
    except Exception as e:
        localdb.rollback()
        return web.json_response({"error": str(e)}, status=204)


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


# async def history_post(request):
#     data = await request.json()
#     progress = Progress(url=data['url'], batch=data['batch'], dept=data['dept'])  # , exam=data['exam'])
#     REQUEST_QUEUE.append(progress)
#     return web.json_response(progress.to_json(), status=201)


async def history_instance_get(request):
    """
    ---
    description: This end-point returns info on a specfic request.
    tags:
    - HISTORY
    responses:
        "200":
            description: successful operation. Returns json containing info.
        "405":
            description: invalid HTTP Method
    """
    request_id = request.match_info['request_id']
    progress = localdb.query(Progress).filter(Progress.id == request_id).first()
    if not progress:
        return web.json_response({'error': 'ERROR:404'}, status=404)
    return web.json_response(progress.to_json(), status=200)


# async def history_instance_put(request, request_id):
#     data = await request.json()
#     progress = localdb.query(Progress).filter(Progress.id == request_id).first()
#     progress.url, progress.batch, progress.dept = data['url'], data['batch'], data['dept']
#     REQUEST_QUEUE.append(progress)
#     return web.json_response(progress, status=201)


async def history_instance_delete(request):
    """
    ---
    description: This end-point deletes a request info (used in case it causes problems to initiate new requests).
    tags:
    - HISTORY
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
        localdb.delete(progress)
        if REQUEST_QUEUE[0].id == progress.id:
            del (REQUEST_QUEUE[0])
            restart_deamon()
        else:
            for i in range(len(REQUEST_QUEUE)):
                if REQUEST_QUEUE[i].id == progress.id:
                    del (REQUEST_QUEUE[i])
        localdb.commit()
    except Exception as e:
        localdb.rollback()
        return web.json_response({"error": str(e)}, status=204)
    return web.json_response(progress.to_json(), status=204)


async def files_get(request):
    """
    ---
    description: This end-point fetches links to all files generated for a particular exam.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation. Returns json .
        "405":
            description: invalid HTTP Method
    """
    return web.json_response({"data": ["list of files"]})  # todo add later


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
    pass


async def url_instance_get(request):
    """
    ---
    description: This end-point  fetches info of url with {url_id}.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    pass


async def exam_get(request):
    """
    ---
    description: This end-point  fetches links to all files generated.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    pass


async def exam_instance_get(request):
    """
    ---
    description: This end-point  fetches info of exam with {exam_id}.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    pass


async def usn_get(request):
    """
    ---
    description: This end-point  fetches all usn records scrapped from beginning along with url_id and exam_id.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation.  Returns json .
        "405":
            description: invalid HTTP Method
    """
    pass


async def usn_instance_get(request):
    """
    ---
    description: This end-point  fetches info of a particular usn record. Takes in url_id and exam_id as get parameters.
    tags:
    - DATA
    responses:
        "200":
            description: successful operation. Returns json .
        "405":
            description: invalid HTTP Method
    """
    pass


# static helpers
async def usn_ui(request):
    """
    ---
    description: This end-point takes in a single USN along with source URL (helper for get internal UI).
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
    description: This end-point takes in a single USN along with source URL (helper for get internal UI).
    tags:
    - DEFAULT UI
    responses:
        "200":
            description: successful operation. Returns a static page.
        "405":
            description: invalid HTTP Method
    """
    print('scrapper.html')
    return web.FileResponse(os.path.join('..', 'default_ui', 'list.html'))


async def batch_ui(request):
    """
    ---
    description: This end-point takes list of USNs along with source URL (helper for get internal UI).
    tags:
    - DEFAULT UI
    responses:
        "200":
            description: successful operation. Returns a static page.
        "405":
            description: invalid HTTP Method
    """
    print('list_ui.html')
    return web.FileResponse(os.path.join('..', 'default_ui', 'batch.html'))


# initialisation helper
def initialise_routes(app):
    app.add_routes(
        [
            static('/DATA', os.path.join('..', 'data', 'files'), show_index=True),
            #get('/ui/batch', batch_ui, allow_head=False),
            #post('/batch', batch_inp),
            get('/ui/test', usn_ui, allow_head=False),
            get('/input/usn', single_usn, allow_head=False),
            get('/ui/list', list_ui, allow_head=False),
            post('/input/list', list_inp),
            get('/queue', queue_get, allow_head=False),
            delete('/queue/{request_id}', queue_cancel),
            get('/history', history_get, allow_head=False),
            get('/history/{request_id}', history_instance_get, allow_head=False),
            delete('/history/{request_id}', history_instance_delete),
            get('/data/url', url_get, allow_head=False),
            get('/data/url/{url_id}', url_instance_get, allow_head=False),
            get('/data/exam', exam_get, allow_head=False),
            get('/data/exam/{exam_id}', exam_instance_get, allow_head=False),
            get('/data/file', files_get, allow_head=False),
            get('/data/usn', usn_get, allow_head=False),
            get('/data/usn/{usn}', usn_instance_get, allow_head=False),
        ]
    )

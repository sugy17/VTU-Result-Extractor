import os
from aiohttp import web
from .. import request_history, request_que, current, my_loop
from ..diagnostics import restart_deamon
from ..executer import async_executer


async def send_stat(request):
    try:
        # print(request.rel_url)
        # url = request.rel_url.query.get('url')
        # batch = request.rel_url.query.get('batch')
        # dept = request.rel_url.query.get('dept')
        # exam = request.rel_url.query.get('exam')
        # request_history[(url, batch, dept, exam)]['queue'] = [i[1] + i[2] for i in request_que]
        if len(current) != 0:
            request_history[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
            return web.json_response(request_history[tuple(current)])
        else:
            return web.json_response({"queue": "No jobs in queue"})
    except Exception as e:
        return web.json_response([str(e)])


async def get_req(request):
    try:
        print(request.rel_url)
        url = request.rel_url.query.get('url')
        batch = request.rel_url.query.get('batch')
        dept = request.rel_url.query.get('dept')
        exam = request.rel_url.query.get('exam')
        if (url, batch, dept, exam) not in request_history or request_history[(url, batch, dept, exam)]['status'] == 'error':
            request_que.append((url, batch, dept, exam))
            request_history[(url, batch, dept, exam)] = {'usn': '-', 'status': 'added'}
        if len(current) == 0:
            current[:] = [url, batch, dept, exam]
        request_history[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
        return web.json_response(request_history[tuple(current)])
    except Exception as e:
        return web.json_response({'msg': 'error'})


async def clear_queue(request):
    try:
        print(request.rel_url)
        for i in request_que:
            del (request_history[i])
        request_que.clear()
        restart_deamon()
        return web.json_response({"msg": "cleared_queue"})
    except Exception as e:
        return web.json_response({'msg': 'error == ' + str(e)})


async def reset(request):
    try:
        print(request.rel_url)
        request_que.clear()
        request_history.clear()
        restart_deamon()
        return web.json_response({"msg": "reinitialised"})
    except Exception as e:
        return web.json_response({'msg': 'error == ' + str(e)})


async def send_res(request):
    try:
        usn = request.rel_url.query.get('usn').lower()
        url = request.rel_url.query.get('url')
        indexpage_url = "/".join(url.split('/')[-2:])
        resultpage_url = indexpage_url.replace('index.php', 'resultpage.php')
        print(request.rel_url)
        #print(indexpage_url,resultpage_url,usn)
        return web.json_response(await async_executer(my_loop, 0, [usn], {}, indexpage_url, resultpage_url, False))
    except Exception as e:
        return web.json_response({'data': 'ops...error-detail:' + str(e)})


async def send_history(request):
    return web.json_response({'msg': 'comming soon'})


async def get_input_list(request):
    return web.json_response({'msg': 'comming soon'})


async def index(request):
    print('scrapper.html')
    return web.FileResponse(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scrapper.html'))


async def usn_ui(request):
    print('scrapper.html')
    return web.FileResponse(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'usn.html'))
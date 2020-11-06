from aiohttp import web
from .. import req_buffer, request_que, current
from ..diagnostics import restart_deamon


async def send_stat(request):
    try:
        print(request.rel_url)
        # url = request.rel_url.query.get('url')
        # batch = request.rel_url.query.get('batch')
        # dept = request.rel_url.query.get('dept')
        # exam = request.rel_url.query.get('exam')
        # req_buffer[(url, batch, dept, exam)]['queue'] = [i[1] + i[2] for i in request_que]
        if len(current) != 0:
            req_buffer[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
            return web.json_response(req_buffer[tuple(current)])
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
        if (url, batch, dept, exam) not in req_buffer or req_buffer[(url, batch, dept, exam)]['status'] == 'error':
            request_que.append((url, batch, dept, exam))
            req_buffer[(url, batch, dept, exam)] = {'usn': '-', 'status': 'added'}
        if len(current) == 0:
            current[:] = [url, batch, dept, exam]
        req_buffer[tuple(current)]['queue'] = [i[1] + i[2] for i in request_que]
        return web.json_response(req_buffer[tuple(current)])
    except Exception as e:
        return web.json_response({'msg': 'error'})


async def clear_queue(request):
    try:
        print(request.rel_url)
        for i in request_que:
            del (req_buffer[i])
        request_que.clear()
        restart_deamon()
        return web.json_response({"msg": "cleared_queue"})
    except Exception as e:
        return web.json_response({'msg': 'error' + str(e)})


async def send_history(request):
    try:
        print(request.rel_url)
        for i in request_que:
            del (req_buffer[i])
        request_que.clear()
        restart_deamon()
        return web.json_response({"msg": "cleared_queue"})
    except Exception as e:
        return web.json_response({'msg': 'error' + str(e)})

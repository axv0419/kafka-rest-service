import json
import asyncio
import sys
import aiohttp
from flask import Flask, current_app,Response

from flask_aiohttp import AioHTTP
from flask_aiohttp.helper import async, websocket

app = Flask(__name__)

aio = AioHTTP(app)

REST_SERVICE_HOST_PORT = sys.environ['REST_SERVICE_HOST_PORT']


@app.route('/echo')
@websocket
def echo():
    while True:
        msg = yield from aio.ws.receive_msg()

        if msg.tp == aiohttp.MsgType.text:
            aio.ws.send_str(msg.data)
        elif msg.tp == aiohttp.MsgType.close:
            print('websocket connection closed')
            break
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s',
                  aio.ws.exception())
            break


@async
def _proxy(*args, **kwargs):
    response = yield from aiohttp.request(
        method=request.method,
        url=request.url.replace(request.host_url, REST_SERVICE_HOST_PORT),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data= kwargs.get('data', request.get_data()),
        cookies=request.cookies,
        allow_redirects=False)

    resp_data = yield from response.read()
    status_code = response.status_code
    
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in response.raw.headers.items()
               if name.lower() not in excluded_headers]

    return (resp_data, status_code, headers)


@app.route('/', defaults={'path': ''},methods=['GET','POST'])
@app.route('/<path:path>',methods=['GET','POST'])
@async
def api():
    (resp_data, status_code, headers) = yield from _proxy()
    response = Response(content, status_code, headers)
    return response


def main():
    aio.run(app, debug=True)

if __name__ == '__main__':
    main()
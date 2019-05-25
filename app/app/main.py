from flask import Flask,request, Response
import requests
import json
import sys
import logging
from flask_cors import CORS

from . import kafka_client,config_manager

application = app = Flask(__name__)
CORS(app)

LOGGER = logging.getLogger(__file__)

def _proxy(*args, **kwargs):
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, rest_url_base),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data= kwargs.get('data', request.get_data()),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    return (resp.content, resp.status_code, headers)


@app.route('/offsets/<string:topic>',methods=['GET'])
def topic_offsets(topic):
    app.logger.info(f'request - {request.remote_addr} {request.method} {request.path}')
    response_data = _KafkaConsumer.get_topic_offsets(topic)
    response = Response(json.dumps(response_data))
    return response

@app.route('/topics/<string:topic>',methods=['POST'])
def topics_post(topic):
    app.logger.info(f'request - {request.remote_addr} {request.method} {request.path}')
    request.on_json_loading_failed = lambda e: ({"error":f"Request data is not good JSON - {e}"})
    payload = request.get_json()
    LOGGER.info(f"payload -{request.is_json} {payload} ")
    records = payload['records']
    headers = dict(remote_ip=request.remote_addr)
    responses = _KafkaProducer.send_records(topic,records,headers)
    response = Response(json.dumps(responses))
    return response
    
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    app.logger.info(f'request - {request.remote_addr} {request.method} {request.path}')
    content,status_code,headers = _proxy()
    print(content,status_code,headers)
    response = Response(content, status_code, headers)
    return response


logging.basicConfig(level=logging.INFO)

APP_CONFIG = config_manager.get_config()

_KafkaProducer = kafka_client.KafkaProducer(APP_CONFIG['kafka_config'])
_KafkaConsumer = kafka_client.KafkaConsumer(APP_CONFIG['kafka_config'])

rest_url_base = APP_CONFIG['rest_proxy']['url']


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  app.run(host="0.0.0.0", debug=True, port=80)
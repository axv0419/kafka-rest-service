import sys
import os

import requests
import json
import logging

from flask import Flask,request, Response, send_from_directory,jsonify,redirect
from flask_cors import CORS

from . import kafka_client,config_manager


STATIC_FOLDER = os.path.abspath(os.environ.get('STATIC_FOLDER','/static'))
application = app = Flask(__name__,static_folder=STATIC_FOLDER,static_url_path='/static')
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

def send_direct(topic):
  LOGGER.info(f'send_direct - {request.remote_addr} {request.method} {request.path}')
  request.on_json_loading_failed = lambda e: ({"error":f"Request data is not good JSON - {e}"})
  payload = request.get_json()
  if payload.get('error',None):
    content,status_code,headers = json.dumps(payload),400,{}
    response = Response(content, status_code, headers)
    return response

  LOGGER.info(f"payload -{request.is_json} {payload} ")

  records = payload['records']
  record_headers = dict(remote_ip=request.remote_addr)
  error,result = _KafkaProducer.send_records(topic,records,record_headers)
  result_text = json.dumps(result)
  if error:
    status_code = 400 if error == 'TOPIC_NOT_FOUND' else 500
    response = Response(result_text, status_code, {"content-type":"application/json"})
    return response
  headers ={"content-type":"application/vnd.kafka.v1+json"}    
  response = Response(result_text, 200, headers)
  return response

@app.route('/healthz',methods=['GET'])
def healthz(topic):
  return jsonify(dict(status="up"))

@app.route('/offsets/<string:topic>',methods=['GET'])
def topic_offsets(topic):
  app.logger.info(f'request - {request.remote_addr} {request.method} {request.path}')
  response_data = _KafkaConsumer.get_topic_offsets(topic)
  response = Response(json.dumps(response_data))
  return response

@app.route('/topics',methods=['GET'])
def topics_list():
  LOGGER.info(f'request - {request.remote_addr} {request.method} {request.path}')
  LOGGER.info(f'Content Type {request.content_type} ')

  error,result = _KafkaProducer.get_topic_list(showInternal=request.args.get("show_internal",'TRUE').upper() \
    not in ['FALSE','NO'])
  result_text = json.dumps(result)
  if error:
    status_code = 400 if error == 'TOPIC_NOT_FOUND' else 500
    response = Response(result_text, status_code, {"content-type":"application/json"})
    return response

  headers ={"content-type":"application/vnd.kafka.v1+json"}    
  response = Response(result_text, 200, headers)
  return response

@app.route('/topics/<string:topic>',methods=['GET'])
def topics_post(topic):
  LOGGER.info(f'request - {request.remote_addr} {request.method} {request.path}')
  LOGGER.info(f'Content Type {request.content_type} ')

  error,result = _KafkaProducer.get_topic_partitions(topic)
  result_text = json.dumps(result)
  if error:
    status_code = 400 if error == 'TOPIC_NOT_FOUND' else 500
    response = Response(result_text, status_code, {"content-type":"application/json"})
    return response

  headers ={"content-type":"application/vnd.kafka.v1+json"}    
  response = Response(result_text, 200, headers)
  return response


@app.route('/topics/<string:topic>',methods=['POST'])
def topics_post(topic):
  LOGGER.info(f'request - {request.remote_addr} {request.method} {request.path}')
  LOGGER.info(f'Content Type {request.content_type} ')
  
  if ( request.content_type.split(';')[0] in ['application/vnd.kafka.json.v1+json','application/json']) \
    or request.headers.get('s-client-type',None) == 'vue' :
    return send_direct(topic)

  content,status_code,headers = _proxy()
  response = Response(content, status_code, headers)
  return response

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
  app.logger.info(f'request - {request.remote_addr} {request.method} {request.path}')
  if path == '' and 'html' in request.headers.get('Accept',None): 
    return redirect('/static/index.html')

  content,status_code,headers = _proxy()
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
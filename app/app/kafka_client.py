import datetime
import time
import sys
import yaml
import json

from confluent_kafka import Producer,Consumer,KafkaError

from collections import defaultdict
import argparse
import traceback
import logging

LOGGER = logging.getLogger(__file__)


class KafkaProducer:
    def __init__(self,conf):
        self.producer = Producer(conf)
    def send_records(self,topic,records,headers):
        responses = []
        def delivery_report(err, msg):
            """ Called once for each message produced to indicate delivery result.
                Triggered by poll() or flush(). """
            if err is not None:
                LOGGER.info('Message delivery failed: {}'.format(err))
            else:
                LOGGER.info('Message delivered {} {} {} [{}] {}'.format( msg.timestamp(),msg.offset(), msg.topic(), msg.partition(), msg.key()))

            response=dict(error = f"{err}" if err else None, 
                report=dict(timestamp=msg.timestamp()[1],partition=msg.partition(),\
                    offset=msg.offset(),key=msg.key().decode('utf-8')))
            responses.append(response)
        LOGGER.info(f"sending records - {records}")
        for record in records:
            data = json.dumps(record["value"])
            key = record.get('key')
            self.producer.produce(topic, data, key=key, callback=delivery_report,headers=headers)
        
        try:
            self.producer.poll(0)
        except:
            traceback.print_exc()
        self.producer.flush()
        LOGGER.info(f"Responses - {responses}")
        return responses

if __name__ == '__main__':
    _KP = KafkaProducer({'bootstrap.servers':'libra:9092'})


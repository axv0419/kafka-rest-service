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

from cachetools import cached, LRUCache, TTLCache

LOGGER = logging.getLogger(__file__)


class KafkaProducer:
    def __init__(self,conf):
        self.producer = Producer(conf)

    @cached(cache=TTLCache(maxsize=1024, ttl=60))
    def get_topic_partition_count(self,topic_name):
        cmd = self.producer.list_topics(topic_name)
        tmd = cmd.topics.get(topic_name,None)
        pcount = 0
        if tmd:
            pcount = len(tmd.partitions)
        return pcount

    def send_records(self,topic,records,headers):
        responses = []
        def delivery_report(err, msg):
            """ Called once for each message produced to indicate delivery result.
                Triggered by poll() or flush(). """
            if err is not None:
                LOGGER.info('Message delivery failed: {}'.format(err))
            else:
                LOGGER.info('Message delivered {} {} {} [{}] {}'.format( msg.timestamp(),msg.offset(), msg.topic(), msg.partition(), msg.key()))

            keystr = None if err or not msg.key() else msg.key().decode('UTF-8') 
            response=dict(
                error = f"{err}" if err else None, 
                status = "PRODUCER_ERROR" if err else "SUCCESS",
                report=dict(timestamp=msg.timestamp()[1],partition=msg.partition(),\
                    offset=msg.offset(),key=keystr))
            responses.append(response)

        partition_count = self.get_topic_partition_count(topic)
        if not partition_count:
            LOGGER.warn(f"Requested topic {topic} does not exist")
            responses = [dict(
                error = f"Topic {topic} does not exist", 
                status = "PRODUCER_ERROR",
                report= None)]
            return responses


        LOGGER.info(f"sending records - {records}")

        for record in records:
            data = json.dumps(record["value"])
            key = record.get('key')
            partition = record.get('partition',None)
            if partition:
                try:
                    partition = int(partition)
                except:
                    partition = 0
            if partition:
                record_partition =  partition % partition_count
                self.producer.produce(topic,value=data,partition=record_partition, key=key, callback=delivery_report,headers=headers)
            else:
                self.producer.produce(topic, data, key=key, callback=delivery_report,headers=headers)
            self.producer.poll(.01)
        self.producer.flush()
        LOGGER.info(f"Responses - {responses}")
        return responses

if __name__ == '__main__':
    _KP = KafkaProducer({'bootstrap.servers':'libra:9092'})


import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
from hbmqtt.client import MQTTClient


class MQTTPublishClient:
    def __init__(self, broker, port, username, password):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password

    def publish_msg(self, topic, msg, qos):
        try:
            publish.single(topic=topic, payload=msg, qos=qos, hostname=self.broker, port=self.port,
                           auth={"username": self.username, "password": self.password})
            return True, "推送成功！"
        except Exception as e:
            return False, f"推送错误！异常原因{e}"

    def sub_msg(self, topic, qos):
        try:
            message = subscribe.simple(topics=[topic], qos=qos, hostname=self.broker, port=self.port,
                                       auth={"username": self.username, "password": self.password}, keepalive=10)
            # print(message.payload.decode('utf-8'))
            try:
                msg = message.payload.decode('utf-8')
            except:
                msg = "消息decode异常。"
            return True, msg
        except Exception as e:
            return False, f"订阅异常！异常原因{e}"


if __name__ == '__main__':
    topic = "/python/mqtt/1"
    topic2 = "/python/mqtt/2"
    topic3 = "/python/mqtt/3"
    broker = 'mqtt.cntepower.com'
    port = 2883
    username = "sll"
    password = "sll"
    mqtt = MQTTPublishClient(broker, port, username, password)
    # taskThread = TaskThread(broker, port, username, password, topic, 0)
    # taskThread.start()
    pool = ThreadPoolExecutor(max_workers=15)
    task1 = pool.submit(mqtt.sub_msg, topic, 0)
    task2 = pool.submit(mqtt.sub_msg, topic2, 0)
    task3 = pool.submit(mqtt.sub_msg, topic3, 0)
    task_list = [task1, task2, task3]
    time.sleep(4)
    msg = json.dumps({"msg": "hello"})
    print(mqtt.publish_msg(topic, msg, 0))
    print(mqtt.publish_msg(topic2, msg, 0))
    # print(mqtt.publish_msg(topic3, 'msg1', 0))
    # pool.shutdown(wait=False)
    # print(wait(task_list, timeout=2.5))

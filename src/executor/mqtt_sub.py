import logging
import asyncio
import threading
import time

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2

from executor.mqtt_publish_client import MQTTPublishClient


async def uptime_coro(topic, qos):
    C = MQTTClient()
    await C.connect(f'mqtt://sll:sll@mqtt.cntepower.com:2883')
    await C.subscribe([
        (topic, qos),
    ])
    try:
        for i in range(0, 1):
            message = await C.deliver_message()
            packet = message.publish_packet
            print(f"{i}:  {packet.variable_header.topic_name} => {packet.payload.data}")
        await C.unsubscribe([topic])
        await C.disconnect()
    except ClientException as ce:
        logging.error("Client exception: %s" % ce)


class TaskThread(threading.Thread):
    def __init__(self, broker, port, username, password, topic, qos):
        super().__init__()
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.qos = qos

    def run(self):
        formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=formatter)
        asyncio.run(uptime_coro(self.topic, self.qos))


if __name__ == '__main__':
    topic = "/python/mqtt"
    broker = 'mqtt.cntepower.com'
    port = 2883
    username = "sll"
    password = "sll"
    taskThread = TaskThread(broker, port, username, password, topic, 0)
    taskThread.start()
    time.sleep(1)
    mqtt = MQTTPublishClient('mqtt.cntepower.com', 2883, "sll", "sll")
    print(mqtt.publish_msg('/python/mqtt', 'msg1', 0))

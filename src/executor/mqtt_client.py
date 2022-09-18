import paho.mqtt.client as mqtt
import time
from paho.mqtt import client as mqtt_client


class MQTTClientClass:
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.username = None
        self.password = None
        self.connect_status = True
        self.connect_error_msg = None
        self.client = mqtt_client.Client("mqtt-" + str(round(time.time() * 1000)))

    def client_connect(self, username, password=None):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d", rc)
                error_type = {
                    1: "Connection refused - incorrect protocol version",
                    2: "Connection refused - invalid client identifier",
                    3: "Connection refused - server unavailable",
                    4: "Connection refused - bad username or password",
                    5: "Connection refused - not authorised",
                    6: "Currently unused"
                }
                self.connect_status = False
                self.connect_error_msg = error_type[rc]

        if password == '':
            password = None
        self.client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.connect(self.broker, self.port)
        return self.connect_status, self.connect_error_msg

    def publish_msg(self, topic, msg, qos):
        while True:
            try:
                result = self.client.publish(topic=topic, payload=msg, qos=qos)
                status = result[0]
                if status == 0:
                    return True, "推送成功！"
                else:
                    return False, "推送失败！"
            except Exception as e:
                return False, f"推送错误！异常原因{e}"


if __name__ == '__main__':
    mqtt = MQTTClientClass('mqtt.cntepower.com', 2883)
    print(mqtt.client_connect("sll", "sll"))
    print(mqtt.publish_msg('/python/mqtt', 'msg1', 0))

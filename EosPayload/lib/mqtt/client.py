from typing import Any, Callable

import paho.mqtt.client as mosquitto

from EosPayload.lib.mqtt import QOS, Topic


class Client(mosquitto.Client):
    
    def __init__(self, host: str, port: int = 1883):
        super(Client, self).__init__(protocol=mosquitto.MQTTv5)
        self.connect(host, port)

    def receive(self) -> int:
        return self.loop_forever()

    def send(self, topic: Topic, payload: str) -> bool:
        msg_info = self.publish(topic, payload, QOS.DELIVER_AT_MOST_ONCE)
        if msg_info.rc != mosquitto.MQTT_ERR_SUCCESS:
            print("MQTT send failed with error code " + msg_info.rc)
            return False
        return True

    def register_subscriber(self, topic: Topic, callback: Callable) -> Any:
        return self.message_callback_add(topic, callback)



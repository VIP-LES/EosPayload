from typing import Callable
import paho.mqtt.client as mosquitto
import threading

from EosLib.packet import Packet

from EosPayload.lib.mqtt import QOS, Topic


class Client(mosquitto.Client):
    
    def __init__(self, host: str, port: int = 1883):
        """ Connects to the MQTT server and spawns a thread for async MQTT operations.
            Connect operation is synchronous / blocking.  Subsequent sends/receives are async.

        :param host: the hostname of the MQTT server
        :param port: the port of the MQTT server
        """
        super(Client, self).__init__(protocol=mosquitto.MQTTv5)
        self.connect(host, port)
        self.loop_start()

    def __del__(self):
        """ cleans up MQTT thread on shutdown """
        self.loop_stop()
        super(Client, self).__del__()

    def send(self, topic: Topic, payload: Packet) -> mosquitto.MQTTMessageInfo:
        """ Send a packet over MQTT.  Will internally queue messages even if not connected.  Will not notify on error.
            Async (Non-Blocking).

        :param topic: the topic to send
        :param payload: the packet to send
        :return: MQTTMessageInfo object, which has a wait_for_publish() method if you want to block on this message
        """
        return self.publish(topic, payload.encode(), QOS.DELIVER_AT_MOST_ONCE)

    def register_subscriber(self, topic: Topic, callback: Callable) -> None:
        """ Receive an MQTT message.
            Starts listening for messages of the Topic and calling Callback on them.
            Async (Non-Blocking).

        :param topic: the topic to filter for
        :param callback: a function taking 3 parameters: (client, userdata, message)
        """
        self.message_callback_add(topic, callback)
        self.subscribe(topic, QOS.DELIVER_AT_MOST_ONCE)

    def get_thread(self) -> threading.Thread | None:
        """ :return: the MQTT background thread or None if none exists """
        return self._thread


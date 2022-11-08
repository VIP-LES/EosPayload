import datetime

from EosPayload.lib.driver_base import DriverBase
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress
import logging
import time

from EosPayload.lib import MQTT_HOST
from EosPayload.lib.mqtt import Topic
from EosPayload.lib.mqtt.client import Client

PORT = "COM1"


class RadioDriver(DriverBase):

    global PORT

    def setup(self) -> None:
        self.port = XBeeDevice(PORT, 9600)
        self.port.open()
        self.remote = RemoteXBeeDevice(self.port, XBee64BitAddress.from_hex_string("0013A20040XXXXXX"))


    @staticmethod
    def get_device_id() -> str:
        return "radio-driver-007"

    def device_read(self, logger: logging.Logger) -> None:
        mqtt = Client(MQTT_HOST)

        def data_receive_callback(xbee_message):
            packet = xbee_message.decode()
            mqtt.send(Topic.HEALTH_HEARTBEAT, packet)

        self.port.add_data_received_callback(data_receive_callback)

        while True:
            time.sleep(1)

        return 0

    def device_command(self, logger: logging.Logger) -> None:
        mqtt = Client(MQTT_HOST)

        def send_via_xbee(transmit_packet):
            self.port.send_data_async(self.remote, transmit_packet)

        mqtt.register_subscriber(Topic.RADIO_TRANSMIT, send_via_xbee)

        return 0


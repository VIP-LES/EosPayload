
import time

import EosLib.packet.packet

from EosPayload.lib.driver_base import DriverBase
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress
import logging

import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header

from EosPayload.lib import MQTT_HOST
from EosPayload.lib.mqtt import Topic
from EosPayload.lib.mqtt.client import Client

PORT = "COM9"
sequence_number = 0


class RadioDriver(DriverBase):

    global PORT

    def setup(self) -> None:
        con = True
        while con:
            try:
                self.port = XBeeDevice(PORT, 9600)
                self.port.open()
                self.remote = RemoteXBeeDevice(self.port, XBee64BitAddress.from_hex_string("13A20041CB89AE")) # on the chip itself there is a number on the top right. It should be 3!
                con = False
            except:
                self.logger.info("radio port not open")
                time.sleep(10)

    @staticmethod
    def get_device_id() -> str:
        return "radio-driver-007"

    def device_read(self, logger: logging.Logger) -> None:
        mqtt = Client(MQTT_HOST)

        # Receives data from radio and sends it to MQTT
        def data_receive_callback(xbee_message):
            packet = xbee_message.data.decode()
            mqtt.send(Topic.HEALTH_HEARTBEAT, packet)

            self.logger.info("Packet received ~~~~~~")
            self.logger.info(packet)

        # Receives data from MQTT and sends it down to ground station according to priority
        def xbee_send_callback(client, userdata, message):
            global sequence_number

            # gets message from MQTT and convert transmit_packet to packet object (look at Thomas code)
            transmit_packet = EosLib.packet.packet.Packet.decode_from_string(message.payload)

            # append transmit header
            new_transmit_header = EosLib.packet.transmit_header.TransmitHeader(sequence_number)
            transmit_packet.transmit_header = new_transmit_header

            # add packet to queue
            priority = transmit_packet.data_header.priority
            # This will likely be another thread

            # sends packet
            self.port.send_data_async(self.remote, transmit_packet)

            # increments sequence_number
            sequence_number = (sequence_number + 1) % 256  # sequence number can't exceed 255

        mqtt.register_subscriber(Topic.RADIO_TRANSMIT, xbee_send_callback)
        self.port.add_data_received_callback(data_receive_callback)
        self.spin()


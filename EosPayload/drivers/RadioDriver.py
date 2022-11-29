from datetime import datetime
from queue import PriorityQueue
import logging
import time

from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress

from EosLib import Device
from EosLib.packet.packet import Packet
from EosLib.packet.transmit_header import TransmitHeader
from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic

class RadioDriver(DriverBase):
    _thread_queue = PriorityQueue()
    sequence_number = 0

    # mapping from destination to mqtt topic
    device_map = {
        Device.RADIO: Topic.RADIO_TRANSMIT
    }

    def setup(self) -> None:
        con = True
        while con:
            try:
                #self.port = XBeeDevice("/dev/ttyUSB2", 9600)
                self.port = XBeeDevice("COM9", 9600)
                self.port.open()
                self.remote = RemoteXBeeDevice(self.port, XBee64BitAddress.from_hex_string(
                    "13A20041CB89AE"))  # on the chip itself there is a number on the top right. It should be 3!
                con = False
            except Exception as e:
                self._logger.error(f"radio port not open: {e}")
                time.sleep(10)

    @staticmethod
    def get_device_id() -> Device:
        return Device.RADIO

    @staticmethod
    def get_device_name() -> str:
        return "radio-driver"

    def device_read(self, logger: logging.Logger) -> None:
        # Receives data from radio and sends it to MQTT
        def data_receive_callback(xbee_message):
            packet = xbee_message.data
            packet_object = Packet.decode(packet)
            mqtt_topic = self.device_map[packet_object.data_header.destination]
            self._mqtt.send(mqtt_topic, packet)

            logger.info("Packet received ~~~~~~")
            logger.info(packet)

        # Receives data from MQTT and sends it down to ground station according to priority
        def xbee_send_callback(client, userdata, message):

            # gets message from MQTT and convert transmit_packet to packet object (look at Thomas code)
            packet_from_mqtt = Packet.decode(message.payload)

            # append transmit header
            new_transmit_header = TransmitHeader(self.sequence_number)
            packet_from_mqtt.transmit_header = new_transmit_header

            # add packet to queue
            priority = packet_from_mqtt.data_header.priority
            logger.info(f"Enqueuing packet seq={self.sequence_number}")
            self._thread_queue.put((priority, datetime.now(), packet_from_mqtt,))

            self.sequence_number = (self.sequence_number + 1) % 256  # sequence number can't exceed 255

        self._mqtt.register_subscriber(Topic.RADIO_TRANSMIT, xbee_send_callback)
        self.port.add_data_received_callback(data_receive_callback)
        self.spin()

    # queue thread stuff
    def device_command(self, logger: logging.Logger) -> None:
        while True:
            (priority, timestamp, packet) = self._thread_queue.get()
            # sends packet
            logger.info(f"Sending packet seq={packet.transmit_header.send_seq_num} to ground")
            self.port.send_data_async(self.remote, packet.encode())

import time

from EosLib.packet.packet import Packet
from EosPayload.lib.driver_base import DriverBase
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress
import logging
from EosLib.packet.transmit_header import TransmitHeader

import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header

from EosPayload.lib.mqtt import Topic
from EosPayload.lib.mqtt.client import Client
from queue import PriorityQueue



import itertools
# import heapq
from datetime import datetime

# pq = []                         # list of entries arranged in a heap
# counter = itertools.count()     # unique sequence count

# def add_packet(priority, packet):
#     'Add a new task or update the priority of an existing task'
#     entry = [priority, datetime.now(), packet]
#     heapq.heappush(pq, entry)
#
#
# def pop_packet():
#     'Remove and return the lowest priority task. Raise KeyError if empty.'
#     if len(pq) != 0:
#         priority, time, packet = heapq.heappop(pq)
#         return packet



class RadioDriver(DriverBase):
    _thread_queue = PriorityQueue()
    def setup(self) -> None:
        con = True
        while con:
            try:
                #self.port = XBeeDevice("/dev/ttyUSB2", 9600)
                self.port = XBeeDevice("COM8", 9600)
                self.port.open()
                self.remote = RemoteXBeeDevice(self.port, XBee64BitAddress.from_hex_string(
                    "13A20041CB89AE"))  # on the chip itself there is a number on the top right. It should be 3!
                con = False
            except:
                self.logger.info("radio port not open")
                time.sleep(10)

    @staticmethod
    def get_device_id() -> str:
        return "radio-driver-007"


    @staticmethod
    def sequence_number(self):
        self.sequence_number = 0


    def device_read(self, logger: logging.Logger) -> None:
        mqtt = Client(self._mqtt)

        # Receives data from radio and sends it to MQTT
        def data_receive_callback(xbee_message):
            packet = xbee_message.data.decode()
            mqtt.send(Topic.HEALTH_HEARTBEAT, packet)

            self.logger.info("Packet received ~~~~~~")
            self.logger.info(packet)

        # Receives data from MQTT and sends it down to ground station according to priority
        def xbee_send_callback(client, userdata, message):

            # gets message from MQTT and convert transmit_packet to packet object (look at Thomas code)
            transmit_packet = Packet.decode_from_string(message.payload)

            # append transmit header
            new_transmit_header = TransmitHeader(self.sequence_number)
            transmit_packet.transmit_header = new_transmit_header

            # add packet to queue
            priority = transmit_packet.data_header.priority
            self._thread_queue.put((priority, datetime.now(), transmit_packet,))

            self.sequence_number = (self.sequence_number + 1) % 256  # sequence number can't exceed 255

        mqtt.register_subscriber(Topic.RADIO_TRANSMIT, xbee_send_callback)
        self.port.add_data_received_callback(data_receive_callback)
        self.spin()

    # queue thread stuff
    def device_command(self, logger: logging.Logger) -> None:
        while True:
            (priority, timestamp, packet) = self._thread_queue.get()
            # sends packet
            self.port.send_data_async(self.remote, packet)



from datetime import datetime
from queue import PriorityQueue

import logging
import pyudev
import time
import traceback

from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress

from EosLib.device import Device
from EosLib.packet.packet import Packet
from EosLib.packet.transmit_header import TransmitHeader
from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic

class RadioDriver(DriverBase):
    _thread_queue = PriorityQueue()
    sequence_number = 0

    # mapping from destination to mqtt topic
    device_map = {
        Device.RADIO: Topic.RADIO_TRANSMIT,
        Device.MISC_RADIO_1: Topic.PING_COMMAND,
        Device.CUTDOWN: Topic.CUTDOWN_COMMAND
    }

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-read', self.device_read)
        self.register_thread('device-command', self.device_command)

        serial_id = "FTDI_XBIB-XBP9XR-0_FT5PG7VE"
        context = pyudev.Context()
        device_list = []
        retries_left = 4
        while retries_left > 0:
            retries_left -= 1
            device_list = list(context.list_devices(ID_SERIAL=serial_id))
            if len(device_list) > 0:
                self._logger.info(f"Detected serial devices: {device_list}")
                break
            else:
                self._logger.error(f"Could not find device.  Retries left: {retries_left}")
                time.sleep(3)

        xbee_node = None
        for device in device_list:
            self._logger.info(f'trying {device.device_node}')
            try:
                self.test_port = XBeeDevice(device.device_node, 9600)
                self.test_port.open()
                self.test_port.send_data_broadcast("Testing")
                xbee_node = device.device_node
                break
            except Exception as e:
                self._logger.info(f"Got exception while trying {device.device_node}: {e}")
            finally:
                self.test_port.close()

        con = True
        while con:
            try:
                self.port = XBeeDevice(xbee_node, 9600)
                self.port.open()
                self.remote = RemoteXBeeDevice(self.port, XBee64BitAddress.from_hex_string(
                    "0013A20041CB8CD8"))  # on the chip itself there is a number on the top right. It should be 4!
                self.remote.disable_acknowledgement = True
                con = False
            except Exception as e:
                self._logger.error(f"radio port not open: {e}")
                time.sleep(10)

    def device_read(self, logger: logging.Logger) -> None:
        # TODO: refactor to move this stuff to setup, a separate thread is pointless
        # Receives data from radio and sends it to MQTT
        def data_receive_callback(xbee_message):
            packet = xbee_message.data  # raw bytearray packet
            logger.info("Packet received ~~~~~~")
            logger.info(packet)
            packet_object = Packet.decode(packet)  # convert packet bytearray to packet object
            dest = packet_object.data_header.destination  # packet object
            if dest in self.device_map:  # mapping from device to mqtt topic
                mqtt_topic = self.device_map[dest]
                self._mqtt.send(mqtt_topic, packet)
            else:
                logger.info("no mqtt destination mapping")

        # Receives data from MQTT and sends it down to ground station according to priority
        def xbee_send_callback(_client, _userdata, message):
            # gets message from MQTT and convert transmit_packet to packet object (look at Thomas code)
            try:
                packet_from_mqtt = Packet.decode(message.payload)

                # append transmit header
                new_transmit_header = TransmitHeader(self.sequence_number)
                packet_from_mqtt.transmit_header = new_transmit_header

                # add packet to queue
                priority = packet_from_mqtt.data_header.priority
                logger.info(f"Enqueuing packet seq={self.sequence_number}")
                self._thread_queue.put((priority, datetime.now(), packet_from_mqtt,))

                self.sequence_number = (self.sequence_number + 1) % 256  # sequence number can't exceed 255
            except Exception as e:
                logger.error(f"Failed to transmit packet: {e}\n{traceback.format_exc()}\n{message.payload}")

        self._mqtt.register_subscriber(Topic.RADIO_TRANSMIT, xbee_send_callback)
        self.port.add_data_received_callback(data_receive_callback)
        self.thread_spin(logger)

    # queue thread stuff
    def device_command(self, logger: logging.Logger) -> None:
        while True:
            # TODO: refactor to be non-blocking so stop signal can be checked
            (priority, timestamp, packet) = self._thread_queue.get()
            logger.info(f":: = {packet.body}")
            try:
                self.port.send_data_async(self.remote, packet.encode(), transmit_options=1)
            except Exception as e:
                self._logger.error(f"exception occurred while attempting to send a packet via radio: {e}"
                                   f"\n{traceback.format_exc()}")

    def cleanup(self):
        self.port.close()
        super().cleanup()


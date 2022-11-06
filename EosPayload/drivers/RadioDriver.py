import datetime

from EosPayload.lib.driver_base import DriverBase
from digi.xbee.devices import XBeeDevice
import logging
import time


import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header

PORT = "COM1"

class RadioDriver(DriverBase):

    global PORT

    def device_read(self, logger: logging.Logger) -> None:

        device = XBeeDevice(PORT, 9600)

        device.open()

        def data_receive_callback(xbee_message):
            print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(),
                                     xbee_message.data.decode()))

            packet_transmit_header = xbee_message.data.decode()

        device.add_data_received_callback(data_receive_callback)

        while True:
            time.sleep(1)

        return 0
    def device_command(self, logger: logging.Logger) -> None:



        return 0

'''
        message = EosLib.packet.packet.Packet()
        message.data_header = EosLib.packet.packet.DataHeader()

        message.data_header.data_type = EosLib.packet.definitions.Type.TELEMETRY
        message.data_header.priority = EosLib.packet.definitions.Priority.DATA
        message.data_header.sender = EosLib.packet.definitions.Device.GPS
        message.data_header.generate_time = datetime.datetime.now()

        message.body = str("All this for a string ?!")

        message.body = message.body.encode()
        # why only encode the body? Why not the entire message?
'''


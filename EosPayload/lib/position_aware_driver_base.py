from abc import ABC

import EosLib.packet.packet
from EosLib import Device, Type
from EosLib.format.Position import Position

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic


class PositionAwareDriverBase(DriverBase, ABC):

    # TODO: Move everything out of init
    def __init__(self):
        super().__init__()
        self.latest_position = Position()
        self._mqtt.subscribe(Topic.POSITION_UPDATE)
        self._mqtt.register_subscriber(Topic.POSITION_UPDATE, self.position_callback)

    def position_callback(self, client, userdata, message):
        incoming_packet = EosLib.packet.packet.Packet.decode(message.payload)
        if (not isinstance(incoming_packet, EosLib.packet.packet.Packet)) or \
                incoming_packet.data_header is None or \
                incoming_packet.data_header.sender != Device.GPS or \
                incoming_packet.data_header.data_type != Type.POSITION:
            return
        else:
            new_position = Position.decode_position(incoming_packet)
            if new_position.valid:
                self.latest_position = new_position

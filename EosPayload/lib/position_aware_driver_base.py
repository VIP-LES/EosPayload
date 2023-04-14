from abc import ABC

import EosLib.packet.packet
from EosLib import Type
from EosLib.device import Device

from EosLib.format.position import Position, FlightState

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic


class PositionAwareDriverBase(DriverBase, ABC):

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.latest_position = Position()

    def setup(self) -> None:
        super().setup()
        self._mqtt.register_subscriber(Topic.POSITION_UPDATE, self.position_callback)

    def position_callback(self, _client, _userdata, message):
        incoming_packet = EosLib.packet.packet.Packet.decode(message.payload)
        if (not isinstance(incoming_packet, EosLib.packet.packet.Packet)) or \
                incoming_packet.data_header is None or \
                incoming_packet.data_header.sender != Device.GPS or \
                incoming_packet.data_header.data_type != Type.POSITION:
            return
        else:
            new_position = Position.decode_position(incoming_packet)
            new_position.flight_state = FlightState(new_position.flight_state)
            if new_position.valid:
                self.latest_position = new_position


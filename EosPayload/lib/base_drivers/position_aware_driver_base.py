from EosLib.device import Device
from EosLib.format import Type
from EosLib.format.formats.position import Position, FlightState
from EosLib.packet import Packet

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic


class PositionAwareDriverBase(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.latest_position: Position | None = Position(None, 0, 0, 0, 0, 0)

    def setup(self) -> None:
        super().setup()
        self._mqtt.register_subscriber(Topic.POSITION_UPDATE, self.position_callback)

    def position_callback(self, _client, _userdata, message):
        incoming_packet = Packet.decode(message.payload)
        if (not isinstance(incoming_packet, Packet)) or \
                incoming_packet.data_header is None or \
                incoming_packet.data_header.sender != Device.GPS or \
                incoming_packet.data_header.data_type != Type.POSITION:
            return
        else:
            new_position: Position = incoming_packet.body
            new_position.flight_state = FlightState(new_position.flight_state)
            if new_position.valid:
                self.latest_position = new_position


import logging
import traceback

import asyncio
import pycyphal
from pycyphal.transport.can import CANTransport
from pycyphal.transport.can.media.socketcan import SocketCANMedia
from pycyphal.transport import (
    PayloadMetadata,
    MessageDataSpecifier,
    InputSessionSpecifier
)

from EosLib.format.formats.e_field import EField
from EosLib.format import Type
from EosLib.packet import Packet
from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority

from EosPayload.lib.base_drivers.driver_base import DriverBase


class ElectricFieldSensor(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)

        # initialize media socket
        media = SocketCANMedia(
            iface_name="can0",  # Use vcan0 for virtual CAN testing
            mtu=64  # 64 bytes = CAN FD mode
        )
        self.transport = CANTransport(
            media,
            local_node_id=43  # FIXME get id from Matthew
        )

        data_spec_a = MessageDataSpecifier(subject_id=1200)
        session_spec_a = InputSessionSpecifier(data_spec_a, remote_node_id=None)

        data_spec_b = MessageDataSpecifier(subject_id=1201)
        session_spec_b = InputSessionSpecifier(data_spec_b, remote_node_id=None)

        data_spec_c = MessageDataSpecifier(subject_id=1202)
        session_spec_c = InputSessionSpecifier(data_spec_c, remote_node_id=None)

        self.sub_a = self.transport.get_input_session(session_spec_a, PayloadMetadata(64))
        self.sub_b = self.transport.get_input_session(session_spec_b, PayloadMetadata(64))
        self.sub_c = self.transport.get_input_session(session_spec_c, PayloadMetadata(64))


    def setup(self) -> None:
        super().setup()
        self.register_thread('device-read', self.device_read)

    async def device_read(self, logger: logging.Logger) -> None:
        # adc_pins = [self.pin_1, self.pin_2, self.pin_3]
        counter = 0

        # FIXME consider whether we need to send every packet or should be every 5 or something
        while True:
            counter += 1
            try:
                # TODO test whether this reads as expected
                voltage_a, voltage_b, voltage_c = await asyncio.gather(
                    self.sub_a.receive(asyncio.get_event_loop().time() + 1.0),
                    self.sub_b.receive(asyncio.get_event_loop().time() + 1.0),
                    self.sub_c.receive(asyncio.get_event_loop().time() + 1.0)
                )
                if voltage_a is not None:
                    efield_obj = EField(
                        voltage_a.fragmented_payload[0],
                        voltage_b.fragmented_payload[0],
                        voltage_c.fragmented_payload[0]
                    )
                    header = DataHeader(
                        data_type=Type.E_FIELD,
                        sender=self.get_device_id(),
                        priority=Priority.DATA
                    )
                    packet = Packet(
                        body=efield_obj,
                        data_header=header,
                    )
                    send(packet.encode())  # FIXME fill in with function to send to pico
            except Exception as e:
                self._logger.info(f"An error occurred while reading voltages: {e}\n{traceback.format_exc()}")
            self.thread_sleep(logger, 1)

    def cleanup(self):
        super(ElectricFieldSensor, self).cleanup()
        

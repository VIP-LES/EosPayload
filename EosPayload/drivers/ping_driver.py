from enum import Enum, unique
import logging
import traceback

from EosLib.format import Type

from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority
from EosLib.packet.packet import Packet

from EosLib.format.formats.ping_format import Ping, PingEnum


from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic

"""
    This driver is just software and doesn't collect data.
    It does two functions:
    (1) Emits regular pings to the ground station
    (2) Replies to ping commands from the ground station
    
    Commands should be a utf8-encoded string.
    Syntax:
        `PING [optional identifier]`
        `ACK [optional identifier from PING]`
        `ERR <message>`
    Identifiers should be short to minimize packet size
"""


class PingDriver(DriverBase):

    def setup(self) -> None:
        super().setup()

        self.register_thread('device-command', self.device_command)

    def device_command(self, logger: logging.Logger) -> None:
        if self._mqtt:
            self._mqtt.user_data_set({'logger': logger})
            self._mqtt.register_subscriber(Topic.PING_COMMAND, self.ping_reply)
        counter = 0
        while True:
            self.ping_ground(counter, logger)
            counter = (counter + 1) % 256
            self.thread_sleep(logger, 60)

    def ping_reply(self, client, user_data, message):
        try:
            try:
                packet = Packet.decode(message.payload)

            except Exception as e:
                user_data['logger'].error(f"failed to decode packet sent to {Topic.PING_COMMAND.value}: {e}")
                return

            decoded_packet = Ping.decode(packet.body.encode())
            command = packet.body.ping
            seq_num = decoded_packet.num

            if command:
                user_data['logger'].info(f"received PING command from device '{packet.data_header.sender}'"
                                         f" with sequence number '{seq_num}'")

                response_header = DataHeader(
                    data_type=Type.PING,
                    sender=self.get_device_id(),
                    priority=Priority.TELEMETRY,
                    destination=packet.data_header.sender
                )

                response = Packet(Ping(PingEnum.ACK, seq_num), response_header)
                client.send(Topic.RADIO_TRANSMIT, response)

            else:
                user_data['logger'].info(f"received ACK for ping from device '{packet.data_header.sender}'"
                                         f" with sequence number '{seq_num}'")

        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing ping_reply: {e}"
                                      f"\n{traceback.format_exc()}")

    def ping_ground(self, counter: int, logger: logging.Logger):
        header = DataHeader(
            data_type=Type.PING,
            sender=self.get_device_id(),
            priority=Priority.TELEMETRY,
        )

        packet = Packet(Ping(PingEnum.PING, counter), header)
        if self._mqtt:
            logger.info(f'pinging ground: Ping {counter}')
            self._mqtt.send(Topic.RADIO_TRANSMIT, packet)

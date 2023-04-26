from enum import Enum, unique
import logging
import time
import traceback

from EosLib import Priority, Type
from EosLib.device import Device

from EosLib.packet.data_header import DataHeader
from EosLib.packet.packet import Packet
from EosPayload.lib.driver_base import DriverBase
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

    @unique
    class Commands(str, Enum):
        PING = "PING"
        ACK = "ACK"
        ERR = "ERR"

    @staticmethod
    def command_thread_enabled() -> bool:
        return True

    def device_command(self, logger: logging.Logger) -> None:
        if self._mqtt:
            self._mqtt.user_data_set({'logger': logger})
            self._mqtt.register_subscriber(Topic.PING_COMMAND, self.ping_reply)
        counter = 0
        while True:
            self.ping_ground(counter, logger)
            counter = counter + 1
            time.sleep(60)

    def ping_reply(self, client, user_data, message):
        try:
            try:
                packet = Packet.decode(message.payload)
            except Exception as e:
                user_data['logger'].error(f"failed to decode packet sent to {Topic.PING_COMMAND.value}: {e}")
                return

            command = packet.body.decode('utf8')
            param = ""
            if ' ' in command:
                command, param = packet.body.decode('utf8').split(' ', 1)

            if command not in [cmd.value for cmd in PingDriver.Commands]:
                user_data['logger'].warning(f"received invalid command '{command}'"
                                            f" from device '{packet.data_header.sender}'")
                response_command = PingDriver.Commands.ERR.value + f" invalid command '{command}': '{packet.body.decode('utf8')}'"
                response_header = DataHeader(
                    data_type=Type.WARNING,
                    sender=self.get_device_id(),
                    priority=Priority.TELEMETRY,
                    destination=packet.data_header.sender
                )
                command_bytes = bytes(response_command, 'utf8')
                if len(command_bytes) > Packet.radio_body_max_bytes:
                    user_data['logger'].warning(f"truncating reply because it exceeds max packet body size")
                    command_bytes = command_bytes[0:Packet.radio_body_max_bytes - 1]
                response = Packet(command_bytes, response_header)
                client.send(Topic.RADIO_TRANSMIT, response.encode())
            elif command == PingDriver.Commands.PING:
                user_data['logger'].info(f"received PING command from device '{packet.data_header.sender}'"
                                         f" with param '{param}'")
                response_command = PingDriver.Commands.ACK.value + (f" {param}" if param else '')
                response_header = DataHeader(
                    data_type=Type.TELEMETRY,
                    sender=self.get_device_id(),
                    priority=Priority.TELEMETRY,
                    destination=packet.data_header.sender
                )
                response = Packet(bytes(response_command, 'utf8'), response_header)
                client.send(Topic.RADIO_TRANSMIT, response.encode())
            elif command == PingDriver.Commands.ERR:
                user_data['logger'].warning(f"received error message from device '{packet.data_header.sender}':"
                                            f" \"{param}\"")
            elif command == PingDriver.Commands.ACK:
                user_data['logger'].info(f"received ACK for ping from device '{packet.data_header.sender}'"
                                         f" with param '{param}'")

        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing ping_reply: {e}"
                                      f"\n{traceback.format_exc()}")

    def ping_ground(self, counter: int, logger: logging.Logger):
        command = f"{PingDriver.Commands.PING.value} {counter}"
        header = DataHeader(
            data_type=Type.TELEMETRY,
            sender=self.get_device_id(),
            priority=Priority.TELEMETRY
        )
        packet = Packet(bytes(command, 'utf8'), header)
        if self._mqtt:
            logger.info("pinging ground: " + command)
            self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode())

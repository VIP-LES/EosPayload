import time
from enum import Enum, unique
import logging

from EosLib import Device, Priority, Type
from EosLib.packet.data_header import DataHeader
from EosLib.packet.packet import Packet
from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic

"""
    This driver is just software and doesn't collect data.
    It does two functions:
    (1) Emits regular pings to the ground station
    (2) Replies to ping commands from the ground station
    
    Command syntax:
        `PING [optional identifier]`
        `ACK [optional identifier from PING]`
        `ERR <message>`
"""


class PingDriver(DriverBase):

    @unique
    class Commands(str, Enum):
        PING = "PING"
        ACK = "ACK"
        ERR = "ERR"

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_RADIO_1

    @staticmethod
    def get_device_name() -> str:
        return "ping-driver"

    def device_command(self, logger: logging.Logger) -> None:
        self._mqtt.user_data_set({'logger': logger})
        self._mqtt.register_subscriber(Topic.PING_COMMAND, self.ping_reply)
        counter = 0
        while True:
            self.ping_ground(counter, logger)
            counter = counter + 1
            time.sleep(60)

    @staticmethod
    def ping_reply(client, user_data, message):
        packet = None
        try:
            packet = Packet.decode(message.payload)
        except Exception as e:
            user_data['logger'].error(f"failed to decode packet sent to {Topic.PING_COMMAND.value}: {e}")
            return

        command, param = packet.body.decode('utf8').split(' ', 1)
        if command not in [cmd.value for cmd in PingDriver.Commands]:
            user_data['logger'].warning(f"received invalid command '{command}'"
                                        f" from device '{packet.data_header.sender}'")
            response_command = PingDriver.Commands.ERR.value + f" invalid command '{command}': '{str(packet.body)}'"
            response_header = DataHeader(
                data_type=Type.WARNING,
                sender=PingDriver.get_device_id(),
                priority=Priority.TELEMETRY,
                destination=packet.data_header.sender
            )
            response = Packet(bytes(response_command, 'utf8'), response_header)
            client.send(Topic.RADIO_TRANSMIT, response.encode())
        elif command == PingDriver.Commands.PING:
            user_data['logger'].info(f"received PING command from device '{packet.data_header.sender}'")
            response_command = PingDriver.Commands.ACK.value + (f" {param}" if param else '')
            response_header = DataHeader(
                data_type=Type.TELEMETRY,
                sender=PingDriver.get_device_id(),
                priority=Priority.TELEMETRY,
                destination=packet.data_header.sender
            )
            response = Packet(bytes(response_command, 'utf8'), response_header)
            client.send(Topic.RADIO_TRANSMIT, response.encode())
        elif command == PingDriver.Commands.ERR:
            user_data['logger'].warning(f"received error message from device '{packet.data_header.sender}':"
                                        f" \"{param}\"")

    def ping_ground(self, counter: int, logger: logging.Logger):
        command = f"{PingDriver.Commands.PING.value} {counter}"
        logger.info("pinging ground: " + command)
        header = DataHeader(
            data_type=Type.TELEMETRY,
            sender=PingDriver.get_device_id(),
            priority=Priority.TELEMETRY,
            destination=Device.RADIO,  # TODO: remove patch for EosLib 0.2.0
        )
        packet = Packet(bytes(command, 'utf8'), header)
        self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode())

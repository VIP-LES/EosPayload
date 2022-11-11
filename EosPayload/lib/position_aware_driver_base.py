import datetime
import struct
from abc import ABC

import EosLib.packet.packet
from EosLib import Device

from EosPayload.lib.driver_base import DriverBase


# TODO: Move this entire thing to EosLib
from EosPayload.lib.mqtt import Topic


class Position:
    # Struct format is: timestamp, lat, long, speed, altitude, number of satellites
    gps_struct_string = "!" \
                        "d" \
                        "d" \
                        "d" \
                        "d" \
                        "d" \
                        "H"

    def __init__(self):
        self.local_time = None
        self.timestamp = None
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.speed = None
        self.number_of_satellites = None
        self.valid = False

    # TODO: figure out a more legitimate way to check validity
    def set_validity(self):
        if (self.number_of_satellites < 4 or
                self.latitude == 0 or
                self.longitude == 0):
            self.valid = False
        else:
            self.valid = True

    @staticmethod
    def decode_position(gps_packet: EosLib.packet.packet.Packet):
        new_position = Position()
        new_position.local_time = datetime.datetime.now()
        new_position.gps_packet = gps_packet
        if new_position.gps_packet.data_header.sender != EosLib.Device.GPS:
            raise ValueError("Packet is not from GPS")

        unpacked_tuple = struct.unpack(Position.gps_struct_string, new_position.gps_packet.body)
        new_position.timestamp = unpacked_tuple[0]
        new_position.latitude = unpacked_tuple[1]
        new_position.longitude = unpacked_tuple[2]
        new_position.altitude = unpacked_tuple[3]
        new_position.speed = unpacked_tuple[4]
        new_position.number_of_satellites = unpacked_tuple[5]
        new_position.set_validity()

        return new_position

    @staticmethod
    def encode_position(timestamp: float, latitude: float, longitude: float, altitude: float, speed: float,
                        number_of_satellites: int) -> bytes:
        return struct.pack(Position.gps_struct_string, timestamp, latitude, longitude, altitude, speed,
                           number_of_satellites)


class PositionAwareDriverBase(DriverBase, ABC):
    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_3

    @staticmethod
    def get_device_name() -> str:
        return "why-is-this-spawning"

    @staticmethod
    def enabled() -> bool:
        return False

    def __init__(self):
        super().__init__()
        self.latest_position = Position()
        self._mqtt.subscribe(Topic.RADIO_TRANSMIT)
        self._mqtt.register_subscriber(Topic.RADIO_TRANSMIT, self.position_callback)

    def position_callback(self, client, userdata, message):
        incoming_packet = EosLib.packet.packet.Packet.decode(message.payload)
        if (not isinstance(incoming_packet, EosLib.packet.packet.Packet)) or\
                incoming_packet.data_header is None or\
                incoming_packet.data_header.sender != Device.GPS:
            return
        else:
            new_position = Position.decode_position(incoming_packet)
            self.latest_position = new_position

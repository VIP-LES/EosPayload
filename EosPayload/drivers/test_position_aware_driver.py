from random import randint
import logging

import EosLib.packet.packet
import serial
import datetime

from EosLib.packet.definitions import Device, Type, Priority

import EosPayload
from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase, Position
from EosPayload.lib.mqtt import MQTT_HOST, Topic


class TestPositionAwareDriver(PositionAwareDriverBase):
    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_2

    @staticmethod
    def get_device_name() -> str:
        return "position-aware-driver"

    def continue_callback(self, client_info, message):
        self.__logger.info("New position time is: {}".format(self.latest_position.timestamp))

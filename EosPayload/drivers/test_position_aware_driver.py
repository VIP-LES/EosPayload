import time
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

    def device_command(self, logger: logging.Logger) -> None:
        old_position = Position()
        while True:
            time.sleep(3)
            if old_position.timestamp != self.latest_position.timestamp:
                logger.info("New position found at {}. Is valid: {}".format(self.latest_position.timestamp,
                                                                            self.latest_position.valid))
                old_position = self.latest_position

import logging
import time

import Adafruit_BBIO.PWM as PWM

from EosLib.format.position import FlightState
from EosLib.packet.definitions import Device

from EosPayload.drivers.reefing_driver import ReefingDriver


class TestReefingDriver(ReefingDriver):
    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_TEST_3

    @staticmethod
    def get_device_name() -> str:
        return "test-reefing-motor-driver"

    def setup(self) -> None:
        self.current_reef_amount = 0

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.update_interval = 5

    def set_reefing_level(self, reefing_percent: float, logger: logging.Logger):
        logger.info(f"Setting reefing to {reefing_percent}%")

import Adafruit_BBIO.GPIO as GPIO
import logging
import time

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class LEDDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_1

    @staticmethod
    def get_device_name() -> str:
        return "led-driver"

    @staticmethod
    def command_thread_enabled() -> bool:
        return True

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.pin_name = "P9_12"

    def setup(self) -> None:
        super(LEDDriver, self).setup()
        GPIO.setup(self.pin_name, GPIO.OUT)

    def device_command(self, logger: logging.Logger) -> None:
        pin_state = 0
        while True:
            GPIO.output(self.pin_name, pin_state)
            pin_state = 1 if 0 else 0
            time.sleep(5)

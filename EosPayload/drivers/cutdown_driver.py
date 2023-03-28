
import logging
import time

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase

import Adafruit_BBIO.GPIO as GPIO

class cutdownDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_2

    @staticmethod
    def get_device_name() -> str:
        return "Cutdown-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def setup(self):
        GPIO.setup("P8_10", GPIO.OUT)

    def device_read(self, logger: logging.Logger) -> None:
        GPIO.output("P8_10", GPIO.LOW)
        logger.info("Countdown")
        for i in range(10):
            logger.info("COUNT: " + str(i))
            time.sleep(1)

        GPIO.output("P8_10", GPIO.HIGH)
        for i in range(5):
            logger.info("COUNT: " + str(i))
            time.sleep(1)

        GPIO.output("P8_10", GPIO.LOW)
        logger.info("END OF TEST")

    def cleanup(self):
        GPIO.cleanup()



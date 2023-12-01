import Adafruit_BBIO.GPIO as GPIO
import logging
from EosPayload.lib.base_drivers.driver_base import DriverBase


class ChrisLEDDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led_1 = "P9_21"
        self.num_blinks = 0

    def setup(self) -> None:
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("failed to import GPIO library")

        self.register_thread('device-command', self.device_command)

        GPIO.setup(self.led_1, GPIO.OUT)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            # Wait 3 Seconds
            GPIO.output(self.led_1, 0)
            self.thread_sleep(logger, 3)

            # Light blinks for 0.5 seconds
            GPIO.output(self.led_1, 1)
            self.thread_sleep(logger, 0.5)

            # Increase Number of Blinks
            self.num_blinks += 1
            self._logger.info(self.num_blinks)

    def cleanup(self):
        try:
            GPIO.output(self.led_1, 0)
            GPIO.cleanup()
        except NameError:
            pass

        super(ChrisLEDDriver, self).cleanup()
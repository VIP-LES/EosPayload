try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase


class IanLEDDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led = "P9_15"
        self.counter = 0

    def setup(self) -> None:
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("failed to import GPIO library")

        self.register_thread('device-command', self.device_command)

        GPIO.setup(self.led, GPIO.OUT)

    def device_command(self, logger: logging.Logger) -> None:
        pin_state = 0
        while True:
            GPIO.output(self.led, pin_state)
            if pin_state == 0:
                pin_state = 1
                self.thread_sleep(logger, 3)
            else:
                self.counter += 1
                pin_state = 0
                logger.info("Cumulative Number of Blinks: " + self.counter)
                self.thread_sleep(logger, 0.5)

    def cleanup(self):
        try:
            GPIO.output(self.led, 0)
            GPIO.cleanup()
        except NameError:
            pass

        super(IanLEDDriver, self).cleanup()

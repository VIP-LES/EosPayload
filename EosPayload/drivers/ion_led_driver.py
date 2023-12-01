try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase

class LEDDriver1(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led = "P9_21"
        self.count = 0

    def setup(self) -> None:
        super().setup()
        try:
            GPIO
        except NameError:
            raise Exception("failed to import GPIO library")
        self.register_thread("led_controller", self.led_controller)
        GPIO.setup(self.led, GPIO.OUT)

    def led_controller(self, logger: logging.Logger) -> None:
        while True:
            GPIO.output(self.led, 1)
            self.thread_sleep(logger, 0.5)
            GPIO.output(self.led, 0)
            self.count += 1
            logger.info(f"blink count: {self.count}")
            self.thread_sleep(logger, 3)

    def cleanup(self):
        try:
            GPIO.output(self.led, 0)
            GPIO.cleanup()
        except NameError:
            pass

        super(LEDDriver, self).cleanup()
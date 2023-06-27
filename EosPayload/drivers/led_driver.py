import Adafruit_BBIO.GPIO as GPIO
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase


class LEDDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.pin_name = "P9_12"

    def setup(self) -> None:
        super(LEDDriver, self).setup()
        self.register_thread('device-command', self.device_command)

        GPIO.setup(self.pin_name, GPIO.OUT)

    def device_command(self, logger: logging.Logger) -> None:
        pin_state = 0
        while True:
            GPIO.output(self.pin_name, pin_state)
            if pin_state == 0:
                pin_state = 1
            else:
                pin_state = 0
            self.thread_sleep(logger, 5)

    def cleanup(self):
        super(LEDDriver, self).cleanup()
        GPIO.output(self.pin_name, 0)

try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase

""" NOT IMPLEMENTED YET
LED_1 -> Red     | GPS Fix
LED_2 -> Orange  | Running
LED_3 -> Green   | Transmitting
"""


class LEDDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led_1 = "P9_21"
        self.led_2 = "P9_23"
        self.led_3 = "P9_25"

    def setup(self) -> None:
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("failed to import GPIO library")

        self.register_thread('device-command', self.device_command)

        GPIO.setup(self.led_1, GPIO.OUT)
        GPIO.setup(self.led_2, GPIO.OUT)
        GPIO.setup(self.led_3, GPIO.OUT)

    def device_command(self, logger: logging.Logger) -> None:
        pin_state = 0
        while True:
            GPIO.output(self.led_1, pin_state)
            if pin_state == 0:
                pin_state = 1
            else:
                pin_state = 0
            self.thread_sleep(logger, 2)

    def cleanup(self):
        GPIO.output(self.led_1, 0)
        GPIO.output(self.led_2, 0)
        GPIO.output(self.led_3, 0)

        GPIO.cleanup()

        super(LEDDriver, self).cleanup()

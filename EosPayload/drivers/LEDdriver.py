import Adafruit_BBIO.GPIO as GPIO
import time
import logging
from EosPayload.lib.base_drivers.driver_base import DriverBase

class LEDdriver(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led_pin = "P9_41"
        self.blink_count = 0
        self.setup()

    def setup(self):
        GPIO.setup(self.led_pin, GPIO.OUT)
        self.register_thread('led-blinker', self.blink_led)

    def blink_led(self, logger):
        while True:
            GPIO.output(self.led_pin, GPIO.HIGH)  # Turn LED on
            GPIO.output(self.led_pin, GPIO.LOW)   # Turn LED off
            self.thread_sleep(logger, 3)
            self.blink_count += 1
            self._logger.info(self.blink_count)


    def cleanup(self):
        try:
            GPIO.output(self.led_pin, 0)
            GPIO.cleanup()
        except NameError:
            pass

        super(LEDdriver, self).cleanup()


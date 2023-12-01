try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase


class TestLedDriver(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.led_1 = "P9_21"

    def setup(self) -> None:
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("Failed to import GPIO Library")

        self.register_thread('test-device-command', self.test_device_command)

        GPIO.setup(self.led_1, GPIO.OUT)

    def test_device_command(self, logger: logging.Logger) -> None:
        pin_state = 0
        count = 0
        while True:
            GPIO.output(self.led_1, pin_state)
            if pin_state == 0:
                pin_state = 1
                count += 1
                self._logger.info(str(count))
            else:
                pin_state = 0
            self.thread_sleep(logger, 3)

    def cleanup(self):
        try:
            GPIO.output(self.led_1, 0)

            GPIO.cleanup()
        except NameError:
            pass

        super(TestLedDriver, self).cleanup()

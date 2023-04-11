import logging
import time

from EosLib.device import Device
from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic

import Adafruit_BBIO.GPIO as GPIO


class CutdownDriver(PositionAwareDriverBase):
    cutdown_pin = "P8_10"
    time_pulled_high = 7  # seconds

    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_3

    @staticmethod
    def get_device_name() -> str:
        return "Cutdown-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def __int__(self):
        self.auto_cutdown_altitude = 21000
        self.has_triggered = False

    def setup(self):
        super().setup()
        GPIO.setup(CutdownDriver.cutdown_pin, GPIO.OUT)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        if self._mqtt:
            self._mqtt.user_data_set({'logger': self._logger})
            self._mqtt.register_subscriber(Topic.CUTDOWN_COMMAND, self.cutdown_trigger_mqtt)

    def device_read(self, logger: logging.Logger) -> None:
        self.cutdown_trigger()
        while True:
            altitude = self.latest_position.altitude
            if altitude > self.auto_cutdown_altitude and not self.has_triggered:
                self.has_triggered = True
                self.cutdown_trigger()

            time.sleep(1)

    def cutdown_trigger(self):
        self._logger.info("~~~PULLING PIN HIGH~~~")
        self._mqtt.send(Topic.RADIO_TRANSMIT, "Starting Cutdown")
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.HIGH)
        time.sleep(CutdownDriver.time_pulled_high)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        self._logger.info("~~~PULLING PIN LOW~~~")
        self._mqtt.send(Topic.RADIO_TRANSMIT, "Ending Cutdown")

    @staticmethod
    def cutdown_trigger_mqtt(client, user_data, message):
        user_data["logger"].info("~~~PULLING PIN HIGH~~~")
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.HIGH)
        time.sleep(CutdownDriver.time_pulled_high)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        user_data["logger"].info("~~~PULLING PIN LOW~~~")

        '''
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
        '''

    def cleanup(self):
        GPIO.cleanup()

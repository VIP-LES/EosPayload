from queue import Queue
import logging
import time

from EosLib.device import Device
from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic

import Adafruit_BBIO.GPIO as GPIO


class CutdownDriver(PositionAwareDriverBase):
    cutdown_pin = "P8_10"
    time_pulled_high = 7  # seconds
    auto_cutdown_altitude = 21000

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.CUTDOWN

    @staticmethod
    def get_device_name() -> str:
        return "Cutdown-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.has_triggered = False
        self._command_queue = Queue()
        self._mqtt.user_data_set({'logger': self._logger, 'queue': self._command_queue})

    def setup(self):
        super().setup()
        GPIO.setup(CutdownDriver.cutdown_pin, GPIO.OUT)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        if self._mqtt:
            self._mqtt.user_data_set({'logger': self._logger})
            self._mqtt.register_subscriber(Topic.CUTDOWN_COMMAND, self.cutdown_trigger_mqtt)

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            try:
                altitude = self.latest_position.altitude
                if not self.has_triggered:
                    if altitude > self.auto_cutdown_altitude:
                        logger.info(f"reached auto cutdown altitude of {self.auto_cutdown_altitude} meters"
                                    f", triggering cutdown")
                        self.has_triggered = True
                        self.cutdown_trigger()
                    elif not self._command_queue.empty():
                        self._command_queue.get(block=False)
                        logger.info("received cutdown command, triggering cutdown")
                        self.has_triggered = True
                        self.cutdown_trigger()
            except TypeError:
                logger.info("No Altitude Data")

            time.sleep(5)

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
        user_data['logger'].info("received cutdown command")
        user_data['queue'].put(1)
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

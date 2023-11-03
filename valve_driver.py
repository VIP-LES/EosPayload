from queue import Queue
import logging
import time

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic

try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass

class ValveDriver(PositionAwareDriverBase):
    valve_pin = "P9_30"  
    time_valve_open = 5  
    auto_valve_altitude = 25000 

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
        self.has_valve_opened = False
        self._command_queue = Queue()

    def setup(self):
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("Failed to import GPIO library")

        self.register_thread('device-read', self.device_read)

        GPIO.setup(ValveDriver.valve_pin, GPIO.OUT)
        GPIO.output(ValveDriver.valve_pin, GPIO.LOW)
        
        if self._mqtt:
            mqtt_logger = logging.getLogger(self._pretty_id + ".valve-subscriber")
            self._mqtt.user_data_set({'logger': mqtt_logger, 'queue': self._command_queue})
            self._mqtt.register_subscriber(Topic.VALVE_COMMAND, self.valve_trigger_mqtt)

    def cleanup(self):
        try:
            GPIO.cleanup()
        except NameError:
            pass
        super().cleanup()

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # Auto valve opening based on altitude
            try:
                altitude = self.latest_position.altitude
                if not self.has_valve_opened and altitude > self.auto_valve_altitude:
                    logger.info(f"Reached auto valve opening altitude of {self.auto_valve_altitude} meters,"
                                f" opening the valve")
                    self.has_valve_opened = True
                    self.valve_trigger()
            except TypeError:
                logger.info("No Altitude Data")

            # Manual valve opening based on command from ground station
            if not self._command_queue.empty():
                self._command_queue.get(block=False)
                logger.info("Received valve open command, opening the valve")
                self.has_valve_opened = True
                self.valve_trigger()

            time.sleep(5)

    def valve_trigger(self):
        self._logger.info("~~~OPENING VALVE~~~")
        GPIO.output(ValveDriver.valve_pin, GPIO.HIGH)
        time.sleep(ValveDriver.time_valve_open)
        GPIO.output(ValveDriver.valve_pin, GPIO.LOW)
        self._logger.info("~~~CLOSING VALVE~~~")

    @staticmethod
    def valve_trigger_mqtt(client, user_data, message):
        user_data['logger'].info("Received valve open command")
        user_data['queue'].put(1)

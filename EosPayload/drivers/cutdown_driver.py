import traceback
from queue import Queue
import logging

from EosLib.packet import Packet

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic
from EosLib.format.formats.cutdown import CutDown
from EosLib.format.definitions import Type

try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass


class CutdownDriver(PositionAwareDriverBase):
    cutdown_pin = "P9_30"
    time_pulled_high = 10  # seconds
    auto_cutdown_altitude = 23000

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
        self.has_triggered = False
        self._command_queue = Queue()

    def setup(self):
        super().setup()

        try:
            GPIO
        except NameError:
            raise Exception("failed to import GPIO library")

        self.register_thread('device-read', self.device_read)

        GPIO.setup(CutdownDriver.cutdown_pin, GPIO.OUT)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        if self._mqtt:
            mqtt_logger = logging.getLogger(self._pretty_id + ".cutdown-subscriber")
            self._mqtt.user_data_set({'logger': mqtt_logger, 'queue': self._command_queue})
            self._mqtt.register_subscriber(Topic.CUTDOWN_COMMAND, self.cutdown_trigger_mqtt)

    def cleanup(self):
        try:
            GPIO.cleanup()
        except NameError:
            pass
        super().cleanup()

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # auto cutdown based on altitude
            try:
                altitude = self.latest_position.altitude
                if not self.has_triggered and altitude > self.auto_cutdown_altitude:
                    logger.info(f"reached auto cutdown altitude of {self.auto_cutdown_altitude} meters"
                                f", triggering cutdown")
                    self.has_triggered = True
                    self.cutdown_trigger()
            except TypeError:
                logger.info("No Altitude Data")

            # manual cutdown based on command from ground station
            if not self._command_queue.empty():
                decoded_msg = self._command_queue.get(block=False)
                logger.info(f"received cutdown command {decoded_msg}, triggering cutdown")
                self.has_triggered = True
                self.cutdown_trigger()

            self.thread_sleep(logger, 5)

    def cutdown_trigger(self):
        self._logger.info("~~~PULLING PIN HIGH~~~")
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.HIGH)
        self.thread_sleep(self._logger, CutdownDriver.time_pulled_high)
        GPIO.output(CutdownDriver.cutdown_pin, GPIO.LOW)
        self._logger.info("~~~PULLING PIN LOW~~~")

    @staticmethod
    def cutdown_trigger_mqtt(client, user_data, message):
        try:

            packet = Packet.decode(message)
            if packet.data_header.data_type != Type.CUTDOWN:
                user_data['logger'].error(f"incorrect type {packet.data_header.data_type}, expected CutDown")
                return

            decoded_msg = CutDown.decode(packet.body)

            user_data['logger'].info(f"received cutdown command {decoded_msg.ack}")
            user_data['queue'].put(decoded_msg.ack)
        except Exception as e:
            user_data['logger'].error(f"Got exception {e}\n{traceback.format_exc()}")

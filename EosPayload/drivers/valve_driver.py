import traceback
from queue import Queue
import logging
import time

from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic
from EosLib.format.formats.valve import Valve
from EosLib.format.definitions import Type
from EosLib.packet import Packet
from EosLib.format.definitions import Type

try:
    import Adafruit_BBIO.GPIO as GPIO
except ModuleNotFoundError:
    pass

class ValveDriver(PositionAwareDriverBase):
    # Electrical team you will have to change this pin because this is currently used by cutdown
    valve_pin = "P9_30"  
    time_valve_open = 5  
    auto_valve_altitude = 17000 

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
                decoded_msg = self._command_queue.get(block=False)
                logger.info(f"Received valve open command {decoded_msg}, opening the valve")
                self.has_valve_opened = True
                self.valve_trigger()

            self.thread_sleep(logger, 5)

    def valve_trigger(self):
        self._logger.info("~~~OPENING VALVE~~~")
        GPIO.output(ValveDriver.valve_pin, GPIO.HIGH)
        self.thread_sleep(self._logger, ValveDriver.time_valve_open)
        GPIO.output(ValveDriver.valve_pin, GPIO.LOW)
        self._logger.info("~~~CLOSING VALVE~~~")

    def valve_trigger_mqtt(self, client, user_data, message):
        try:
            # packet = Packet.decode(message.payload)
            # if packet.data_header.data_type != Type.VALVE:
            #     user_data['logger'].error(f"incorrect type {packet.data_header.data_type}, expected Valve")
            #     return
            #
            # decoded_msg = Valve.decode(packet.body.encode())
            #
            # user_data['logger'].info(f"Received valve command {decoded_msg.ack}")
            # user_data['queue'].put(decoded_msg.ack)
            #
            # response_header = DataHeader(
            #     data_type=Type.VALVE,
            #     sender=self.get_device_id(),
            #     priority=Priority.URGENT,
            #     destination=packet.data_header.sender
            # )
            #
            # response = Packet(Valve(decoded_msg.ack), response_header)
            # client.send(Topic.RADIO_TRANSMIT, response)
            #
            # user_data['logger'].info(f"Received ACK for valve from device '{packet.data_header.sender}'"
            #                          f" with sequence number '{decoded_msg.ack}'")
            #
            # user_data['logger'].info(f"received valve open command {decoded_msg.ack}")
            # user_data['queue'].put(decoded_msg.ack)

            packet = Packet.decode(message.payload)
            if packet.data_header.data_type != Type.VALVE:
                user_data['logger'].error(f"Incorrect type {packet.data_header.data_type}, expected Valve")
                return

            decoded_msg = Valve.decode(packet.body.encode())

            user_data['logger'].info(f"Received valve command {decoded_msg.ack}")
            user_data['queue'].put(decoded_msg.ack)

            response_header = DataHeader(
                data_type=Type.VALVE,
                sender=self.get_device_id(),
                priority=Priority.URGENT,
                destination=packet.data_header.sender
            )

            response = Packet(Valve(decoded_msg.ack), response_header)
            client.send(Topic.RADIO_TRANSMIT, response)

            user_data['logger'].info(f"Received ACK for valve from device '{packet.data_header.sender}'"
                                     f" with sequence number '{decoded_msg.ack}'")

        except Exception as e:
            user_data['logger'].error(f"Got exception {e}\n{traceback.format_exc()}")

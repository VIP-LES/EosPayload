import logging
import time
import traceback

import board
from adafruit_ms8607 import MS8607

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase

class SensorDriver(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_1

    @staticmethod
    def get_device_name() -> str:
        return "Sensor Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        i2c = board.I2C()
        ms = MS8607(i2c)
        count = 0
        while True:
            try:
                temp = ms.temperature
            except Exception as e:
                logger.critical("A fatal exception occurred when attempting to get temperature data"
                                f": {e}\n{traceback.format_exc()}")

            csv_row = [temp]

            # this saves data to a file
            try:
                self.data_log(csv_row)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            if count % 2 == 0:
                try:
                    self.data_transmit(csv_row)
                    #time.sleep(1)
                except Exception as e:
                    logger.error(f"unable to transmit data: {e}")

            count += 1
            time.sleep(1)

    @staticmethod
    def enabled() -> bool:
        return True
from random import randint
import logging
import time

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase

# This example shows a very basic polled driver that logs data to CSV and transmits it to ground


class TestDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_TEST_1

    @staticmethod
    def get_device_name() -> str:
        return "test-driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            data = randint(0, 256)
            csv_row = [str(data), str(data*data)]

            # this saves data to a file
            try:
                self.data_log(csv_row)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                self.data_transmit(csv_row)
            except Exception as e:
                logger.error(f"unable to transmit data: {e}")

            time.sleep(3)

    @staticmethod
    def enabled() -> bool:
        return False

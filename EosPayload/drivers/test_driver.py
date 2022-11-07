import logging
import time
from random import randint

from EosPayload.lib.driver_base import DriverBase


class TestDriver(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "test-driver-001"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            data = randint(0, 256)
            self.data_log([str(data), str(data*data)])
            time.sleep(3)

    @staticmethod
    def enabled() -> bool:
        return False

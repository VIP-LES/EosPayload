import logging
import time
from random import randint
from smbus2 import SMBus

from EosPayload.lib.driver_base import DriverBase


class ProofOfConceptDriver(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "temp-driver-proof-of-concept-002"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(2)
            b = bus.read_byte_data(77, 0)
            self.data_log([str(b)])
            time.sleep(3)

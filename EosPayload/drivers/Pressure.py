import logging
import time
from random import randint
from smbus2 import SMBus, i2c_msg

from EosPayload.lib.driver_base import DriverBase



class PressureDriver(DriverBase):

    #I2C
    @staticmethod
    def get_device_id() -> str:
        return "Pressure"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(1)
            b = bus.read_byte_data(80, 0)
            data = b
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

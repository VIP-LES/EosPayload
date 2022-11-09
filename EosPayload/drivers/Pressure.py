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
    #I2C
    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(2)
            b = bus.read_i2c_block_data(0x76, 0x88, 24)
            str_b = list(map(str, b))
            self.data_log(str_b)
            time.sleep(3)

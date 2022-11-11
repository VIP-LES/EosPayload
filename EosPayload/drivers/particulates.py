import logging
import time
from smbus2 import SMBus


from random import randint

from EosPayload.lib.driver_base import DriverBase

#I2C

class Particulates(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Particulates"
    #I2C
    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(3)
            b = bus.read_i2c_block_data(0x69, 0x88, 24)
            str_b = list(map(str, b))
            self.data_log(str_b)
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            bus = SMBus(3)
            b = bus.read_i2c_block_data(0x69, 0x88, 24)
            bus.write_i2c_block_data(0x69, 0, b)
        return 0

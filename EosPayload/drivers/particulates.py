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
            bus = SMBus(1)
            b = bus.read_byte_data(80, 0)
            data = b
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        return 0

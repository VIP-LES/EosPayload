import logging
import time
from smbus2 import SMBus, i2c_msg

from EosPayload.lib.driver_base import DriverBase



class LightVisible(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Light visible uva"

    # I2C
    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # this is where you would poll a device for data
            bus = SMBus(1)
            b = bus.read_byte_data(80, 0)
            data = b
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

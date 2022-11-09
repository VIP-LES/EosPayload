import logging
import time

from smbus2 import SMBus

from EosPayload.lib.driver_base import DriverBase


class LightIR(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "IR Light"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(2)
            b = bus.read_i2c_block_data(0x29, 0x88, 24)
            str_b = list(map(str, b))
            self.data_log(str_b)
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

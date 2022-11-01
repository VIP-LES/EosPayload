import logging
import time
from random import randint

from EosPayload.lib.driver_base import DriverBase

"AIN4", "P9_33"
"AIN6", "P9_35"
"AIN5", "P9_36"
"AIN2", "P9_37"
"AIN3", "P9_38"
"AIN0", "P9_39"
"AIN1", "P9_40"



class PressureDriver(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Pressure"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            data = randint(0, 256)
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        logger.info("Starting to send a command!")
        while True:
            # this is where you would send a command to device
            data = randint(0, 256)
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

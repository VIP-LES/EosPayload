import logging
import time

from random import randint

from EosPayload.lib.driver_base import DriverBase


class TempHumidity(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Temp + Humidity"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data
            data = randint(0, 256)
            self.data_log([str(data), str(data * data)])
            time.sleep(3)
    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

import logging
import time

from random import randint

from EosPayload.lib.driver_base import DriverBase


class Particulates(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Particulates"

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # this is where you would poll a device for data or whatever
            data = randint(0, 256)
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

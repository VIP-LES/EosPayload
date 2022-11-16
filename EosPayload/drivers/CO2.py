import logging
import time
from EosPayload.lib.driver_base import DriverBase


class CO2(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "C02"

    # analog
    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # this is where you would poll a device for data or whatever

            data = 0
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

    @staticmethod
    def enabled() -> bool:
        return False

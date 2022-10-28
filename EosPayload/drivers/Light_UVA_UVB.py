import logging
import time

from random import randint

from EosPayload.lib.driver_base import DriverBase


class LightUVAUVB(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Light UVA UVB"

    def device_read(self, logger: logging.Logger) -> None:
        data = randint(0, 256)
        time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

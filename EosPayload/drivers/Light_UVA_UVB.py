import logging
import time
<<<<<<< HEAD
from EosPayload.lib.driver_base import DriverBase
import Adafruit_BBIO.ADC as ADC

ADC.setup()
=======

from random import randint

from EosPayload.lib.driver_base import DriverBase
>>>>>>> cb26e7dccb714ba4b1fd748296d82615d3b64994


# ADC
class LightUVAUVB(DriverBase):

    @staticmethod
    def get_device_id() -> str:
        return "Light UVA UVB"

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            # this is where you would poll a device for data or whatever
<<<<<<< HEAD
            value = ADC.read_raw("P9_39")
=======
            value = 0
>>>>>>> cb26e7dccb714ba4b1fd748296d82615d3b64994
            data = value
            self.data_log([str(data), str(data * data)])
            time.sleep(3)

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

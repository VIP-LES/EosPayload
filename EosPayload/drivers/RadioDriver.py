from EosPayload.lib.driver_base import DriverBase
import logging
#import digi-xbee


class RadioDriver(DriverBase):
    def device_read(self, logger: logging.Logger) -> None:
        return 0
    def device_command(self, logger: logging.Logger) -> None:
        return 0


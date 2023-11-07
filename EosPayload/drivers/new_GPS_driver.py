import serial
import logging

from ublox_gps import UbloxGps

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class NewGPSDriver(PositionAwareDriverBase):

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
        self.uart = None
        self.gps = None

    def setup(self) -> None:
        super().setup()

        self.register_thread('device-read', self.device_read)
        self.uart = serial.Serial('/dev/ttyO1', baudrate=9600, timeout=1)
        self.gps = UbloxGps(self.uart)

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting NEW GPS Driver!")
        while True:
            try:
                coords = self.gps.geo_coords()
                logger.info(coords.lon)
                logger.info(coords.lat)
            except (ValueError, IOError) as err:
                logger.info(err)

    def cleanup(self):
        if self.uart:
            self.uart.close()
        super().cleanup()

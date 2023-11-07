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
            if not self.gps.satellites() < 3:
                logger.info("Waiting for fix...")
                self.thread_sleep(logger, 1)
                continue

            gps_time = self.gps.date_time()
            time_sec = gps_time.sec
            time_min = gps_time.min
            time_hr = gps_time.hour
            time_day = gps_time.day
            time_month = gps_time.month
            time_year = gps_time.year

            #time_min = self.gps.timestamp_utc.tm_min
            #time_sec = self.gps.timestamp_utc.tm_sec
            #time_day = self.gps.timestamp_utc.tm_mday
            #time_month = self.gps.timestamp_utc.tm_mon
            #time_year = self.gps.timestamp_utc.tm_year


            #try:
            #    coords = self.gps.geo_coords()
            #    logger.info(coords.lon)
            #    logger.info(coords.lat)
            #except (ValueError, IOError) as err:
            #    logger.info(err)

    def cleanup(self):
        if self.uart:
            self.uart.close()
        super().cleanup()

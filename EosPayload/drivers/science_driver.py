import logging
import time
import busio
import traceback
from EosPayload.lib.base_drivers.driver_base import DriverBase

from adafruit_pm25.i2c import PM25_I2C
from adafruit_blinka.microcontroller.am335x import pin

import adafruit_tsl2591
import adafruit_ltr390
import adafruit_shtc3
import adafruit_bmp3xx

class ScienceDriver(DriverBase):

    @staticmethod
    def read_thread_enabled() -> bool:
        return False

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.count = 0
        self.i2c = None
        self.sht = None
        self.bmp = None
        self.ltr = None
        self.tsl = None
        self.pm25 = None

    def setup(self) -> None:
        super().setup()
        self.i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)

        self.sht = adafruit_shtc3.SHTC3(self.i2c)
        self.bmp = adafruit_bmp3xx.BMP3XX_I2C(self.i2c)
        self.ltr = adafruit_ltr390.LTR390(self.i2c)
        self.tsl = adafruit_tsl2591.TSL2591(self.i2c)
        self.pm25 = PM25_I2C(self.i2c)

    def device_read(self, logger: logging.Logger) -> None:

        logger.info("Starting to poll for science data!")

        while True:
            time.sleep(1)

            try:
                row = []

                # base sensor readout
                row.append(str(self.sht.temperature))
                row.append(str(self.sht.relative_humidity))
                row.append(str(self.bmp.pressure))
                row.append(str(self.bmp.altitude))
                row.append(str(self.ltr.light))
                row.append(str(self.ltr.uvs))
                row.append(str(self.ltr.uvi))
                row.append(str(self.ltr.lux))
                row.append(str(self.tsl.infrared))
                row.append(str(self.tsl.visible))
                row.append(str(self.tsl.full_spectrum))

                aqdata = self.pm25.read()
                for i in aqdata.values():
                    row.append(str(i))

            except Exception as e:
                logger.error(f"An unhandled exception occurred while reading data from sensors: {e}"
                                      f"\n{traceback.format_exc()}")

            try:
                '''
                READING THE CSV FILE
                base sensors make up the first 9 columns:
                    temperature (C), relative humidity, pressure (hPa), altitude (m), ambient light, uv, uv index, lux, infrared,
                    visible light, full spectrum (IR + vis)

                pm25 (air quality) makes up the next 12:
                    concentration units (standard): pm 1.0, pm 2.5, pm 10.0, concentration units (environmental): pm 1.0, pm 2.5, pm 10.0,
                    particles > 0.3um / 0.1L air, > 0.5um, > 1.0um, > 2.5um, > 5.0um, > 10.0um
                '''
                self.data_log(row)
            except Exception as e:
                logger.error(f"An unhandled exception occurred while logging data: {e}"
                                      f"\n{traceback.format_exc()}")

            if self.count % 2 == 0:
                try:
                    self.data_transmit(row)
                except Exception as e:
                    logger.error(f"An unhandled exception occurred while transmitting data: {e}"
                                      f"\n{traceback.format_exc()}")

            self.count += 1
            time.sleep(1)

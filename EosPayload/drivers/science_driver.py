import logging
import time
import board
import busio
from EosPayload.lib.driver_base import DriverBase
from EosLib.device import Device

from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import Adafruit_BBIO.ADC as ADC
from adafruit_blinka.microcontroller.am335x import pin

import adafruit_tsl2591
import adafruit_ltr390
import adafruit_shtc3
import adafruit_bmp3xx

class ScienceDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_3

    @staticmethod
    def get_device_name() -> str:
        return "science-driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)

        # base sensors
        sht = adafruit_shtc3.SHTC3(i2c)
        bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)
        ltr = adafruit_ltr390.LTR390(i2c)
        tsl = adafruit_tsl2591.TSL2591(i2c)
        
        # research sensors
        pm25 = PM25_I2C(i2c)
        # ADC.setup()
        logger.info("Starting to poll for science data!")


        while True:
            time.sleep(1)

            try:
                row = []

                # base sensor readout
                row.append(str(sht.temperature))
                row.append(str(sht.relative_humidity))
                row.append(str(bmp.pressure))
                row.append(str(bmp.altitude))
                row.append(str(ltr.light))
                row.append(str(ltr.uvs))
                row.append(str(ltr.uvi))
                row.append(str(ltr.lux))
                row.append(str(tsl.infrared))
                row.append(str(tsl.visible))
                row.append(str(tsl.full_spectrum))

                aqdata = pm25.read()
                for i in aqdata.values():
                    row.append(str(i))

            except RuntimeError:
                logger.info("Unable to read from sensor, retrying...")
                logger.info("Hello")
                continue

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
                logger.error(f"Unable to log data: {e}")

            if count % 2 == 0:
                try:
                    self.data_transmit(row)
                except Exception as e:
                    logger.error(f"Unable to transmit data: {e}")

            count += 1
            time.sleep(1)
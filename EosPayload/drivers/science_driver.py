import logging
import time
import board
import busio
from EosPayload.lib.driver_base import DriverBase
from EosLib.device import Device

from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import Adafruit_BBIO.ADC as ADC

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
        i2c = busio.I2C(board.SCL, board.SDA)

        # base sensors
        sht = adafruit_shtc3.SHTC3(i2c)
        ltr = adafruit_ltr390.LTR390(i2c)
        tsl = adafruit_tsl2591.TSL2591(i2c)
        # bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)

        # research sensors
        # reset_pin = None
        # pm25 = PM25_I2C(i2c, reset_pin)
        ADC.setup()
        analogPin = "P9_40"
        logger.info("Starting to poll for science data!")


        while True:
            time.sleep(1)

            try:
                # base sensor readout
                logger.info("Temperature (science): {} C".format(sht.temperature))
                logger.info("Relative Humidity: {}".format(sht.relative_humidity))
                logger.info("Ambient Light: {}".format(ltr.light))
                logger.info("UV: {}".format(ltr.uvs))
                logger.info("UV Index: {}".format(ltr.uvi))
                logger.info("Lux: {}".format(ltr.lux))
                logger.info("Infrared: {}".format(tsl.infrared))
                logger.info("Visible Light: {}".format(tsl.visible))
                logger.info("Full Spectrum (IR + vis): {}".format(tsl.full_spectrum))

                # logger.info("Pressure: {} hPa".format(bmp.pressure))
                # logger.info("Altitude: {} m".format(bmp.altitude))

                # research sensor readout
                potVal = ADC.read(analogPin)
                potVolt = potVal * 1.8
                logger.info("radioactivity: {}".format(potVolt))


                # aqdata = pm25.read()
                # logger.info("Concentration Units (standard)")
                # logger.info("---------------------------------------")
                # logger.info(
                #     "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
                #     % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
                # )
                # logger.info("Concentration Units (environmental)")
                # logger.info("---------------------------------------")
                # logger.info(
                #     "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
                #     % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
                # )
                # logger.info("---------------------------------------")
                # logger.info("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
                # logger.info("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
                # logger.info("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
                # logger.info("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
                # logger.info("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
                # logger.info("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
                # logger.info("---------------------------------------")

            except RuntimeError:
                logger.info("Unable to read from sensor, retrying...")
                logger.info("Hello")
                continue
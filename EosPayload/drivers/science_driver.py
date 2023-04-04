import logging
import time
import board
import busio
from EosPayload.lib.driver_base import DriverBase
from EosLib.device import Device

from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C

import adafruit_tmp117
import adafruit_ltr390

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
        # reset_pin = None
        i2c = busio.I2C(board.SCL, board.SDA)
        # tmp = adafruit_tmp117.TMP117(i2c)
        ltr = adafruit_ltr390.LTR390(i2c)
        # pm25 = PM25_I2C(i2c, reset_pin)
        logger.info("Starting to poll for science data!")


        while True:
            time.sleep(1)

            try:
                # logger.info("Temperature (science): {}".format(tmp.temperature))
                logger.info("Light: {}".format(ltr.light))
                # aqdata = pm25.read()
                # logger.info(aqdata)
            except RuntimeError:
                logger.info("Unable to read from sensor, retrying...")
                logger.info("Hello")
                continue

            '''
            logger.info("Concentration Units (standard)")
            logger.info("---------------------------------------")
            logger.info(
                "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
                % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
            )
            logger.info("Concentration Units (environmental)")
            logger.info("---------------------------------------")
            logger.info(
                "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
                % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
            )
            logger.info("---------------------------------------")
            logger.info("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
            logger.info("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
            logger.info("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
            logger.info("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
            logger.info("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
            logger.info("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
            logger.info("---------------------------------------")
            '''
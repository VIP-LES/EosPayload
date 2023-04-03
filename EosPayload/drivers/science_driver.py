import logging
import time
import board
import busio
from EosPayload.lib.driver_base import DriverBase
from EosLib.device import Device

from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C

# test with bno
# TODO delete later
from adafruit_bno055 import BNO055_I2C
from adafruit_blinka.microcontroller.am335x import pin

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

    # TODO delete
    def __int__(self):
        self.i2c = None
        self.bno = None

    def device_read(self, logger: logging.Logger) -> None:
        reset_pin = None
        i2c = busio.I2C(board.SCL, board.SDA)
        pm25 = PM25_I2C(i2c, reset_pin)

        # TODO delete
        self.i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)
        self.bno = BNO055_I2C(self.i2c)


        while True:
            time.sleep(1)

            try:
                # TODO delete
                temperature = self.bno.temperature
                x_rotation = self.bno.euler[0]
                y_rotation = self.bno.euler[1]
                z_rotation = self.bno.euler[2]
                logger.info("Euler angle: (SCIENCE) {}".format(self.bno.euler))
                logger.info("Temperature: {} (SCIENCE) degrees C".format(self.bno.temperature))
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

import logging
import traceback

import board
import adafruit_ms8607
from adafruit_ms8607 import MS8607
from adafruit_tsl2591 import TSL2591
from adafruit_ltr390 import LTR390

from smbus2 import SMBus

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class I2CDriver(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_3

    @staticmethod
    def get_device_name() -> str:
        return "I2C-Driver-2"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        i2c = board.I2C()
        ms = MS8607(i2c)
        tsl = TSL2591(i2c)
        ltr = LTR390(i2c)

        try:
            while True:
                # temp = ms.temperature
                # light_vis = tsl.visible
                # light_inf = tsl.infrared
                # light_visuva = ltr.light
                try:
                    temp = ms.temperature
                except Exception as e:
                    temp = -1
                    logger.critical("A fatal exception occurred when attempting to get temperature data"
                                    f": {e}\n{traceback.format_exc()}")

                try:
                    light_vis = tsl.visible
                except Exception as e:
                    light_vis = -1
                    logger.critical("A fatal exception occurred when attempting to get visible light data"
                                    f": {e}\n{traceback.format_exc()}")

                try:
                    light_inf = tsl.infrared
                except Exception as e:
                    light_inf = -1
                    logger.critical("A fatal exception occurred when attempting to get infrared light data"
                                    f": {e}\n{traceback.format_exc()}")

                try:
                    light_visuva = ltr.light
                except Exception as e:
                    light_visuva = -1
                    logger.critical("A fatal exception occurred when attempting to get visible uva data"
                                    f": {e}\n{traceback.format_exc()}")

                a = [temp, light_vis, light_inf, light_visuva]  # array of data
                data = [str(i) for i in a]  # data into string array
                self.data_log(data)  # puts row into csv
                self.data_transmit(data)
        except Exception as e:
            logger.error(f"unable to transmit data: {e}")








    # def device_command(self, logger: logging.Logger) -> None:
    #     logger.info("Starting to send command to device!")
    #     while True:
    #         # this is where you would send command to device
    #         bus = SMBus(2)
    #         bus.write_i2c_block_data(0x44, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return False

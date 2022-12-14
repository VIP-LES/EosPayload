import logging
import time
import traceback

import board
from adafruit_ms8607 import MS8607
from adafruit_tsl2591 import TSL2591
from adafruit_ltr390 import LTR390

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class I2CDriver(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_1

    @staticmethod
    def get_device_name() -> str:
        return "I2C-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        i2c = board.I2C()
        # ms = MS8607(i2c)
        tsl = TSL2591(i2c)
        ltr = LTR390(i2c)
        count = 0
        while True:

            # while True:
            #     print("Pressure: %.2f hPa" % sensor.pressure)
            #     print("Temperature: %.2f C" % sensor.temperature)
            #     print("Humidity: %.2f %% rH" % sensor.relative_humidity)

            # try:
            #     rh = ms.relative_humidity
            #     pres = ms.pressure
            #     temp = ms.temperature
            #     rh_str = str(round(rh, 3))
            #     pres_str = str(round(pres, 3))
            #     temp_str = str(round(temp, 3))
            # except Exception as e:
            #     rh_str = '-1'
            #     pres_str = '-1'
            #     temp_str = '-1'
            #     logger.critical("A fatal exception occurred when attempting to get temp/humidity/pressure data"
            #                     f": {e}\n{traceback.format_exc()}")

            try:
                lux = tsl.lux
                infrared = tsl.infrared
                visible = tsl.visible
                full_spectrum = tsl.full_spectrum
                lux_str = str(round(lux, 3))
                infrared_str = str(round(infrared, 3))
                visible_str = str(round(visible, 3))
                full_spectrum_str = str(round(full_spectrum, 3))
            except Exception as e:
                lux_str = '-1'
                infrared_str = '-1'
                visible_str = '-1'
                full_spectrum_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get Light (IR Visible) data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                uv = ltr.uvs
                amb_light = ltr.light
                uv_str = str(round(uv, 3))
                amb_light_str = str(round(amb_light, 3))
            except Exception as e:
                uv_str = '-1'
                amb_light_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get Light (Visible UVA) data"
                                f": {e}\n{traceback.format_exc()}")

            csv_row = [lux_str, infrared_str, visible_str, full_spectrum_str, uv_str, amb_light_str]

            # this saves data to a file
            try:
                self.data_log(csv_row)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            if count % 2 == 0:
                try:
                    self.data_transmit(csv_row)
                    #time.sleep(1)
                except Exception as e:
                    logger.error(f"unable to transmit data: {e}")

            count += 1
            time.sleep(1)

    @staticmethod
    def enabled() -> bool:
        return True

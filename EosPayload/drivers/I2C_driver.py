from random import randint
import logging
import time
import traceback

import board
from adafruit_ms8607 import MS8607
from adafruit_tsl2591 import TSL2591
from adafruit_ltr390 import LTR390

from smbus2 import SMBus

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class I2CDriver(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_1

    @staticmethod
    def get_device_name() -> str:
        return "I2C-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        i2c = board.I2C()
        ms = MS8607(i2c)
        tsl = TSL2591(i2c)
        ltr = LTR390(i2c)
        while True:
            # this is where you would poll a device for data or whatever
            # bus = SMBus(2)

            # while True:
            #     print("Pressure: %.2f hPa" % sensor.pressure)
            #     print("Temperature: %.2f C" % sensor.temperature)
            #     print("Humidity: %.2f %% rH" % sensor.relative_humidity)

            try:
                # th = bus.read_i2c_block_data(0x40, 0xF5, 16)  # Relative Humidity RH (MS8607)
                rh = ms.relative_humidity
                rh_str = str(round(rh, 3))
            except Exception as e:
                # th = -1
                rh_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get temp & humidity data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                # pr = bus.read_i2c_block_data(0x76, 0x00, 24)  # Pressure & Temperature (MS8607)
                pres = ms.pressure
                temp = ms.temperature
                pres_str = str(round(pres, 3))
                temp_str = str(round(temp, 3))
            except Exception as e:
                # pr = -1
                pres_str = '-1'
                temp_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get pressure data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                # irv_low_byte = bus.read_i2c_block_data(0x29, 0x14, 16)  # Light (IR Visible), alternative address: 0x28
                # irv_high_byte = bus.read_i2c_block_data(0x29, 0x15, 16) # (TSL2591)
                # irv = (irv_high_byte << 8) + irv_low_byte
                lux = tsl.lux
                infrared = tsl.infrared
                visible = tsl.visible
                full_spectrum = tsl.full_spectrum
                lux_str = str(round(lux, 3))
                infrared_str = str(round(infrared, 3))
                visible_str = str(round(visible, 3))
                full_spectrum_str = str(round(full_spectrum, 3))
            except Exception as e:
                # irv = -1
                lux_str = '-1'
                infrared_str = '-1'
                visible_str = '-1'
                full_spectrum_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get Light (IR Visible) data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                # vuva = bus.read_i2c_block_data(0x53, 0xA7, 20)  # Light (Visible UVA) (LTR390)
                uv = ltr.uvs
                amb_light = ltr.light
                uv_str = str(round(uv, 3))
                amb_light_str = str(round(amb_light, 3))
            except Exception as e:
                # vuva = -1
                uv_str = '-1'
                amb_light_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get Light (Visible UVA) data"
                                f": {e}\n{traceback.format_exc()}")

            # csv_row1 = [str(i) for i in th]
            # csv_row2 = [str(i) for i in pr]
            # csv_row3 = [str(i) for i in irv]
            # csv_row4 = [str(i) for i in vuva]

            csv_row1 = [rh_str]
            csv_row2 = [pres_str, temp_str]
            csv_row3 = [lux_str, infrared_str, visible_str, full_spectrum_str]
            csv_row4 = [uv_str, amb_light_str]

            # this saves data to a file
            try:
                self.data_log(csv_row1)
                self.data_log(csv_row2)
                self.data_log(csv_row3)
                self.data_log(csv_row4)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                self.data_transmit(csv_row1)
                self.data_transmit(csv_row2)
                self.data_transmit(csv_row3)
                self.data_transmit(csv_row4)
            except Exception as e:
                logger.error(f"unable to transmit data: {e}")

            time.sleep(0.5)

    # def device_command(self, logger: logging.Logger) -> None:
    #     logger.info("Starting to send command to device!")
    #     while True:
    #         # this is where you would send command to device
    #         bus = SMBus(2)
    #         bus.write_i2c_block_data(0x44, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True

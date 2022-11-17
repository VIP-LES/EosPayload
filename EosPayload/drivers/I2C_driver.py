from random import randint
import logging
import time
import traceback
from smbus2 import SMBus
from datetime import datetime

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
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(2)
            try:
                th = bus.read_i2c_block_data(0x44, 0x88, 24)  # Temperature & Humidity
            except Exception as e:
                th = -1
                logger.critical("A fatal exception occurred when attempting to get temp & humidity data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                pr = bus.read_i2c_block_data(0x76, 0x88, 24)  # Pressure, alternative address: 0x40
            except Exception as e:
                pr = -1
                logger.critical("A fatal exception occurred when attempting to get pressure data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                pa = bus.read_i2c_block_data(0x69, 0x88, 24)  # Particulates
            except Exception as e:
                pa = -1
                logger.critical("A fatal exception occurred when attempting to get particulates data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                irv = bus.read_i2c_block_data(0x29, 0x88, 24)  # Light (IR Visible), alternative address: 0x28
            except Exception as e:
                irv = -1
                logger.critical("A fatal exception occurred when attempting to get Light (IR Visible) data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                vuva = bus.read_i2c_block_data(0x53, 0x88, 24)  # Light (Visible UVA)
            except Exception as e:
                vuva = -1
                logger.critical("A fatal exception occurred when attempting to get Light (Visible UVA) data"
                                f": {e}\n{traceback.format_exc()}")

            # str_th = list(map(str, th))
            # str_pr = list(map(str, pr))
            # str_pa = list(map(str, pa))
            # str_irv = list(map(str, irv))
            # str_vuva = list(map(str, vuva))
            # csv_row = [str_th, str_pr, str_pa, str_irv, str_vuva]
            csv_row = [str(th), str(pr), str(pa), str(irv), str(vuva)]
            # csv_row1 = [str_th]
            # csv_row2 = [str_pr]
            # csv_row3 = [str_pa]
            # csv_row4 = [str_irv]
            # csv_row5 = [str_vuva]

            # this saves data to a file
            try:
                self.data_log(csv_row)
                # self.data_log(csv_row1)
                # self.data_log(csv_row2)
                # self.data_log(csv_row3)
                # self.data_log(csv_row4)
                # self.data_log(csv_row5)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                self.data_transmit(csv_row)
                # self.data_transmit(csv_row1)
                # self.data_transmit(csv_row2)
                # self.data_transmit(csv_row3)
                # self.data_transmit(csv_row4)
                # self.data_transmit(csv_row5)
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
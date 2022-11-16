from random import randint
import logging
import time
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
            bus = SMBus(0)
            th = bus.read_i2c_block_data(0x44, 0x88, 24)  # Temperature & Humidity
            pr = bus.read_i2c_block_data(0x76, 0x88, 24)  # Pressure, alternative address: 0x40
            pa = bus.read_i2c_block_data(0x69, 0x88, 24)  # Particulates
            irv = bus.read_i2c_block_data(0x29, 0x88, 24)  # Light (IR Visible), alternative address: 0x28
            vuva = bus.read_i2c_block_data(0x53, 0x88, 24)  # Light (Visible UVA)
            str_th = list(map(str, th))
            str_pr = list(map(str, pr))
            str_pa = list(map(str, pa))
            str_irv = list(map(str, irv))
            str_vuva = list(map(str, vuva))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_th),
                       str(str_pr), str(str_pa), str(str_irv), str(str_vuva)]

            # this saves data to a file
            try:
                self.data_log(csv_row)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                self.data_transmit(csv_row)
            except Exception as e:
                logger.error(f"unable to transmit data: {e}")

            time.sleep(0.5)

    # def device_command(self, logger: logging.Logger) -> None:
    #     logger.info("Starting to send command to device!")
    #     while True:
    #         # this is where you would send command to device
    #         bus = SMBus(1)
    #         bus.write_i2c_block_data(0x44, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True

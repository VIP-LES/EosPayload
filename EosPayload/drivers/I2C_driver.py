from random import randint
import logging
import time
from smbus2 import SMBus
from datetime import datetime

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class TempHumidity(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.TEMPERATURE_HUMIDITY

    @staticmethod
    def get_device_name() -> str:
        return "TempHumidity-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(0)
            b = bus.read_i2c_block_data(0x44, 0x88, 24)
            str_b = list(map(str, b))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_b)]

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


class Pressure(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.PRESSURE

    @staticmethod
    def get_device_name() -> str:
        return "Pressure-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(0)
            b = bus.read_i2c_block_data(0x76, 0x88, 24)  # or 0x40
            str_b = list(map(str, b))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_b)]

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
    #         bus.write_i2c_block_data(0x76, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True


class Particulates(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.PARTICULATES

    @staticmethod
    def get_device_name() -> str:
        return "Particulates-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(0)
            b = bus.read_i2c_block_data(0x69, 0x88, 24)
            str_b = list(map(str, b))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_b)]

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
    #         bus.write_i2c_block_data(0x69, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True


class IRLight(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.IR_VISIBLE_LIGHT

    @staticmethod
    def get_device_name() -> str:
        return "IRLight-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(0)
            b = bus.read_i2c_block_data(0x29, 0x88, 24)  # or 0x28
            str_b = list(map(str, b))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_b)]

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
    #         bus.write_i2c_block_data(0x29, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True


class LightVisibleUVA(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.VISIBLE_UVA_LIGHT

    @staticmethod
    def get_device_name() -> str:
        return "LightVisibleUVA-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            bus = SMBus(0)
            b = bus.read_i2c_block_data(0x53, 0x88, 24)
            str_b = list(map(str, b))
            now = datetime.now()
            dt_string = now.strftime(" %d/%m/%Y %H:%M:%S ")
            csv_row = [str(self.get_device_name()), str(dt_string), str(str_b)]

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
    #         bus.write_i2c_block_data(0x53, 0x88, 24)
    #         time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True

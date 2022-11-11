from random import randint
import logging
import time

import EosLib.packet.packet
import serial
import datetime

from EosLib.packet.definitions import Device, Type, Priority
from EosPayload.lib.driver_base import DriverBase


class EngineeringDataDriver(DriverBase):
    esp_data_format = ["HR:MM:SEC", "MONTH/DAY", "LAT", "LONG", "speed", "altitude", "#ofSatellites", "accInX",
                       "accInY", "accInZ", "gyroX", "gyroY", "gyroZ", "IMU-temp", "pressure", "BME-temp",
                       "humidity"]
    esp_data_time_format = "%H:%M:%S %m/%d/%Y"

    def __init__(self):
        super().__init__()
        self.esp_port = "/dev/ttyUSB0"
        self.esp_baud = 115200
        self.ser_connection = None
        self.emit_rate = datetime.timedelta(seconds=1)

    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_1

    @staticmethod
    def get_device_name() -> str:
        return "engineering-data-driver"

    @staticmethod
    def process_raw_esp_data(raw_data) -> ([str], dict):
        list_data = raw_data.strip().split(',')
        data_dict = dict(zip(EngineeringDataDriver.esp_data_format, list_data))

        # TODO: Find a better solution for the year before 2023 please
        data_datetime_string = data_dict["HR:MM:SEC"] + " " + data_dict["MONTH/DAY"] + "/2022"
        data_datetime = datetime.datetime.strptime(data_datetime_string, EngineeringDataDriver.esp_data_time_format)
        data_dict['datetime'] = str(data_datetime.timestamp())

        return list_data, data_dict

    def setup(self) -> None:
        self.ser_connection = serial.Serial(self.esp_port, self.esp_baud)

    def fetch_data(self) -> str:  # This function might seem weird, but it exists to make mocking easier
        return self.ser_connection.readline()

    def is_alive(self):
        return self.ser_connection.isopen()

    def device_read(self, logger: logging.Logger) -> None:
        last_emit_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while self.is_alive():
            incoming_raw_data = self.fetch_data()
            incoming_processed_data, incoming_data_dict = self.process_raw_esp_data(incoming_raw_data)
            self.data_log(incoming_processed_data)

    def cleanup(self):
        self.ser_connection.close()

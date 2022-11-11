from random import randint
import logging

import EosLib.packet.packet
import serial
import datetime

from EosLib.packet.definitions import Device, Type, Priority

import EosPayload
from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase, Position
from EosPayload.lib.mqtt import MQTT_HOST, Topic


class EngineeringDataDriver(PositionAwareDriverBase):
    esp_data_format = ["HR:MM:SEC", "MONTH/DAY", "LAT", "LONG", "speed", "altitude", "#ofSatellites", "accInX",
                       "accInY", "accInZ", "gyroX", "gyroY", "gyroZ", "IMU-temp", "pressure", "BME-temp",
                       "humidity"]
    esp_data_time_format = "%H:%M:%S %m/%d/%Y"

    # TODO: Move everything out of init
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
        list_data = raw_data.replace('\x00', '').split(',')
        data_dict = dict(zip(EngineeringDataDriver.esp_data_format, list_data))

        # TODO: Find a better solution for the year before 2023 please
        data_datetime_string = data_dict["HR:MM:SEC"] + " " + data_dict["MONTH/DAY"] + "/2022"
        data_datetime = datetime.datetime.strptime(data_datetime_string, EngineeringDataDriver.esp_data_time_format)
        data_dict['datetime'] = str(data_datetime.timestamp())
        data_dict['LAT'].replace('N', '').replace('S', '')
        data_dict['LONG'].replace('E', '').replace('W', '')

        return list_data, data_dict

    def setup(self) -> None:
        self.ser_connection = serial.Serial(self.esp_port, self.esp_baud)

    def fetch_data(self) -> str:  # This function might seem weird, but it exists to make mocking easier
        return self.ser_connection.readline().decode()

    def is_alive(self):
        return self.ser_connection.isOpen()

    def emit_data(self, data_dict, logger):
        gps_packet = EosLib.packet.packet.Packet()
        gps_packet.data_header = EosLib.packet.packet.DataHeader()
        gps_packet.data_header.sender = Device.GPS
        gps_packet.data_header.data_type = Type.TELEMETRY
        gps_packet.data_header.priority = Priority.TELEMETRY

        gps_packet.body = Position.encode_position(float(data_dict['datetime']), float(data_dict['LAT']),
                                                   float(data_dict['LONG']), float(data_dict['altitude']),
                                                   float(data_dict['speed']), int(data_dict['#ofSatellites']))

        self._mqtt.send(Topic.RADIO_TRANSMIT, gps_packet.encode())
        logger.info("Emitting position")

    def device_read(self, logger: logging.Logger) -> None:
        last_emit_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while self.is_alive():
            incoming_raw_data = self.fetch_data()
            incoming_processed_data, incoming_data_dict = self.process_raw_esp_data(incoming_raw_data)
            self.data_log(incoming_processed_data)
            if (datetime.datetime.now() - last_emit_time) > self.emit_rate:
                last_emit_time = datetime.datetime.now()
                self.emit_data(incoming_data_dict, logger)

    def cleanup(self):
        self.ser_connection.close()

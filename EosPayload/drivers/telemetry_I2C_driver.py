import logging
import time

import busio
import board
from adafruit_bno055 import BNO055_I2C
from datetime import datetime

from EosLib.device import Device

from EosLib.packet.data_header import DataHeader
from EosLib import Priority, Type
from EosLib.packet.packet import Packet

from EosPayload.lib.driver_base import DriverBase
from EosLib.format.telemetry_data import TelemetryData
#from adafruit_blinka.microcontroller.am335x import pin
from EosPayload.lib.mqtt import Topic


class TelemetryI2CDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_3

    @staticmethod
    def get_device_name() -> str:
        return "Telemetry-I2C-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def __int__(self):
        self.i2c = None
        self.bno = None

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        #self.i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)
        self.i2c = i2c = busio.I2C(board.SCL, board.SDA)
        self.bno = BNO055_I2C(self.i2c)
        count = 0

        while True:

            # get data from BNO055
            try:
                temperature = self.bno.temperature
                x_rotation = self.bno.euler[0]
                y_rotation = self.bno.euler[1]
                z_rotation = self.bno.euler[2]
                logger.info("Euler angle: {}".format(self.bno.euler))
                logger.info("Temperature: {} degrees C".format(self.bno.temperature))
            except:
                temperature, x_rotation, y_rotation, z_rotation = -1

            current_time = datetime.now()

            pressure = -1
            humidity = -1

            telemetry_obj = TelemetryData(current_time, temperature, pressure, humidity, x_rotation, y_rotation, z_rotation)
            telemetry_bytes = telemetry_obj.encode()

            header = DataHeader(
                data_type=Type.TELEMETRY,
                sender=self.get_device_id(),
                priority=Priority.TELEMETRY,
            )

            packet = Packet(
                body=telemetry_bytes,
                data_header=header,
            )
            logger.info(packet)
            self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode())

            count += 1
            time.sleep(2)


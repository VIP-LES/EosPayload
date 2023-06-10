import logging
import time

import busio
from adafruit_bno055 import BNO055_I2C
from datetime import datetime

from EosLib.packet.data_header import DataHeader
from EosLib import Priority, Type
from EosLib.packet.packet import Packet

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosLib.format.telemetry_data import TelemetryData
from adafruit_blinka.microcontroller.am335x import pin
from EosPayload.lib.mqtt import Topic


class TelemetryI2CDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.bno = None
        self.i2c = None

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        self.i2c = busio.I2C(pin.I2C2_SCL, pin.I2C2_SDA)
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

            self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode())

            count += 1
            time.sleep(2)


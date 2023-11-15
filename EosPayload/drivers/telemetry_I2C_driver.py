import logging
import traceback
try:
    import board
except NotImplementedError:
    pass
import busio
from adafruit_bno055 import BNO055_I2C
from datetime import datetime
import adafruit_mprls

from EosLib.format import Type
from EosLib.format.formats.telemetry_data import TelemetryData
from EosLib.packet import Packet
from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic


class TelemetryI2CDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.bno = None
        self.i2c = None
        self.mpr = None

    def setup(self) -> None:
        super().setup()

        try:
            board
        except NameError:
            raise Exception("failed to import board library")

        self.register_thread('device-read', self.device_read)

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.bno = BNO055_I2C(self.i2c)
        self.mpr = adafruit_mprls.MPRLS(self.i2c, psi_min=0, psi_max=25)
        count = 0

        while True:

            # get data from BNO055
            try:
                temperature = self.bno.temperature
                x_rotation = self.bno.euler[0]
                y_rotation = self.bno.euler[1]
                z_rotation = self.bno.euler[2]
            except Exception as e:
                logger.error(f"failed to retrieve data from sensor: {e}\n{traceback.format_exc()}")
                self.thread_sleep(logger, 2)
                continue

            try:
                self.data_log([str(temperature), str(round(x_rotation, 4)),
                               str(round(y_rotation, 4)), str(round(z_rotation, 4))])
            except Exception as e:
                logger.warning(f"exception occurred while logging data: {e}\n{traceback.format_exc()}")

            current_time = datetime.now()

            pressure = self.mpr.pressure
            humidity = -1

            logger.info(f"Temperature: {temperature}\n")

            try:
                telemetry_obj = TelemetryData(temperature, pressure, humidity, x_rotation, y_rotation, z_rotation)
            except Exception as e:
                logger.error(f"exception occurred while logging data: {e}\n{traceback.format_exc()}")
                self.thread_sleep(logger, 2)
                continue
            
            header = DataHeader(
                data_type=Type.TELEMETRY_DATA,
                sender=self.get_device_id(),
                priority=Priority.TELEMETRY,
            )
            packet = Packet(
                body=telemetry_obj,
                data_header=header,
            )
            self._mqtt.send(Topic.RADIO_TRANSMIT, packet)

            count += 1
            self.thread_sleep(logger, 2)


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
from adafruit_blinka.microcontroller.am335x import pin
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

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)

        bno = BNO055_I2C(i2c)
        count = 0

        while True:

            # get data from BNO055
            try:
                temperature = bno.temperature
                x_rotation = bno.euler[0]
                y_rotation = bno.euler[1]
                z_rotation = bno.euler[2]
                logger.info("Euler angle: {}".format(bno.euler))
                logger.info("Temperature: {} degrees C".format(bno.temperature))
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



            #packet_data = data.encode()
            #self._mqtt.send(Topic.RADIO_TRANSMIT, packet_data)


            # while True:
            #    print("Pressure: %.2f hPa" % sensor.pressure)
            #    print("Temperature: %.2f C" % sensor.temperature)
            #    print("Humidity: %.2f %% rH" % sensor.relative_humidity)

            # try:
            #    rh = ms.relative_humidity
            #    pres = ms.pressure
            #    temp = ms.temperature
            #    rh_str = str(round(rh, 3))
            #    pres_str = str(round(pres, 3))
            #    temp_str = str(round(temp, 3))
            # except Exception as e:
            #    rh_str = '-1'
            #    pres_str = '-1'
            #    temp_str = '-1'
            #    logger.critical("A fatal exception occurred when attempting to get temp/humidity/pressure data"
            #                    f": {e}\n{traceback.format_exc()}")

            # try:
            #     lux = tsl.lux
            #     infrared = tsl.infrared
            #     visible = tsl.visible
            #     full_spectrum = tsl.full_spectrum
            #     lux_str = str(round(lux, 3))
            #     infrared_str = str(round(infrared, 3))
            #     visible_str = str(round(visible, 3))
            #     full_spectrum_str = str(round(full_spectrum, 3))
            # except Exception as e:
            #     lux_str = '-1'
            #     infrared_str = '-1'
            #     visible_str = '-1'
            #     full_spectrum_str = '-1'
            #     logger.critical("A fatal exception occurred when attempting to get Light (IR Visible) data"
            #                     f": {e}\n{traceback.format_exc()}")
            # try:
            #     uv = ltr.uvs
            #     amb_light = ltr.light
            #     uv_str = str(round(uv, 3))
            #     amb_light_str = str(round(amb_light, 3))
            # except Exception as e:
            #     uv_str = '-1'
            #     amb_light_str = '-1'
            #     logger.critical("A fatal exception occurred when attempting to get Light (Visible UVA) data"
            #                     f": {e}\n{traceback.format_exc()}")

            # csv_row = [lux_str, infrared_str, visible_str, full_spectrum_str, uv_str, amb_light_str]

            # csv_row = [temp]

            # this saves data to a file
            # try:
            #    self.data_log(csv_row)
            # except Exception as e:
            #    logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            # if count % 2 == 0:
            #    try:
            #        self.data_transmit(csv_row)
            # time.sleep(1)
            #    except Exception as e:
            #        logger.error(f"unable to transmit data: {e}")

            count += 1
            time.sleep(1)

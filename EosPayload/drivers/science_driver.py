import logging
import time
import busio
import traceback
from EosPayload.lib.base_drivers.driver_base import DriverBase

from adafruit_pm25.i2c import PM25_I2C
from adafruit_blinka.microcontroller.am335x import pin

import adafruit_tsl2591
import adafruit_ltr390
import adafruit_shtc3
import adafruit_bmp3xx


class ScienceDriver(DriverBase):

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.count = 0
        self.i2c_bus = None
        self.temp_humidity_sensor = None
        self.barometer = None
        self.uv_light_sensor = None
        self.ir_light_sensor = None
        self.air_quality_sensor = None

    def setup(self) -> None:
        super().setup()
        self.i2c_bus = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)

        self.temp_humidity_sensor = adafruit_shtc3.SHTC3(self.i2c_bus)
        self.barometer = adafruit_bmp3xx.BMP3XX_I2C(self.i2c_bus)
        self.uv_light_sensor = adafruit_ltr390.LTR390(self.i2c_bus)
        self.ir_light_sensor = adafruit_tsl2591.TSL2591(self.i2c_bus)
        self.air_quality_sensor = PM25_I2C(self.i2c_bus)

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for science data!")

        while True:
            time.sleep(1)

            row = []
            try:
                # base sensor readout
                row = [
                    str(self.temp_humidity_sensor.temperature),
                    str(self.temp_humidity_sensor.relative_humidity),
                    str(self.barometer.pressure),
                    str(self.barometer.altitude),
                    str(self.uv_light_sensor.light),
                    str(self.uv_light_sensor.uvs),
                    str(self.uv_light_sensor.uvi),
                    str(self.uv_light_sensor.lux),
                    str(self.ir_light_sensor.infrared),
                    str(self.ir_light_sensor.visible),
                    str(self.ir_light_sensor.full_spectrum),
                ]

                for value in self.air_quality_sensor.read().values():
                    row.append(str(value))

            except Exception as e:
                logger.error(f"An unhandled exception occurred while reading data from sensors: {e}"
                             f"\n{traceback.format_exc()}")

            if len(row) > 0:
                try:
                    '''
                    READING THE CSV FILE
                    base sensors make up the first 9 columns:
                        temperature (C), relative humidity, pressure (hPa), altitude (m), ambient light, uv, uv index,
                        lux, infrared, visible light, full spectrum (IR + vis)

                    pm25 (air quality) makes up the next 12:
                        concentration units (standard): pm 1.0, pm 2.5, pm 10.0,
                        concentration units (environmental): pm 1.0, pm 2.5, pm 10.0,
                        particles > 0.3um / 0.1L air, > 0.5um, > 1.0um, > 2.5um, > 5.0um, > 10.0um
                    '''
                    self.data_log(row)
                except Exception as e:
                    logger.error(f"An unhandled exception occurred while logging data: {e}\n{traceback.format_exc()}")

                if self.count % 5 == 0:
                    # only transmit once every 5s
                    try:
                        self.data_transmit(row)
                    except Exception as e:
                        logger.error(f"An unhandled exception occurred while transmitting data: {e}"
                                     f"\n{traceback.format_exc()}")

                self.count += 1

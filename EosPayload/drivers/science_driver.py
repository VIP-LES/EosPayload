from busio import I2C
from datetime import datetime
import logging
import traceback

try:
    from adafruit_blinka.microcontroller.am335x import pin
except RuntimeError:
    pass

from adafruit_bmp3xx import BMP3XX_I2C
from adafruit_ltr390 import LTR390
from adafruit_pm25.i2c import PM25_I2C
from adafruit_shtc3 import SHTC3
from adafruit_tsl2591 import TSL2591

from EosLib.format import Type
from EosLib.format.formats.science_data import ScienceData
from EosLib.packet import Packet
from EosLib.packet.definitions import Priority
from EosLib.packet.data_header import DataHeader

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic


class ScienceDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.count = 0
        self.i2c_bus: I2C | None = None
        self.temp_humidity_sensor: SHTC3 | None = None
        self.barometer: BMP3XX_I2C | None = None
        self.uv_light_sensor: LTR390 | None = None
        self.ir_light_sensor: TSL2591 | None = None
        self.air_quality_sensor: PM25_I2C | None = None

    def setup(self) -> None:
        super().setup()

        try:
            pin
        except NameError:
            raise Exception("failed to import pin library")

        self.register_thread('device-read', self.device_read)

        self.i2c_bus = I2C(pin.I2C1_SCL, pin.I2C1_SDA)

        self.temp_humidity_sensor = SHTC3(self.i2c_bus)
        self.barometer = BMP3XX_I2C(self.i2c_bus)
        self.uv_light_sensor = LTR390(self.i2c_bus)
        self.ir_light_sensor = TSL2591(self.i2c_bus)
        self.air_quality_sensor = PM25_I2C(self.i2c_bus)

    def cleanup(self):
        if self.i2c_bus is not None:
            self.i2c_bus.deinit()
        super().cleanup()

    def device_read(self, logger: logging.Logger) -> None:

        logger.info("Starting to poll for science data!")

        while True:
            data = None
            try:
                # base sensor readout
                '''
                READING THE CSV FILE
                base sensors make up the first 9 columns:
                    temperature (C), relative humidity, pressure (hPa), altitude (m), ambient light, uv, uv index,
                    lux, infrared, visible light, full spectrum (IR + vis)

                pm25 (air quality) makes up the next 12:
                    concentration units (standard): pm 1.0, pm 2.5, pm 10.0,
                    concentration units (environmental): pm 1.0, pm 2.5, pm 10.0,
                    particles > 0.3um / 0.1L air, > 0.5um, > 1.0um, > 2.5um, > 5.0um, > 10.0um

                    From library docs: Note that “standard” concentrations are those when corrected to standard
                    atmospheric conditions (288.15 K, 1013.25 hPa), and “environmental” concentrations are those
                    measured in the current atmospheric conditions.
                '''
                air_quality_data = list(self.air_quality_sensor.read().values())
                data = ScienceData(
                    temperature_celsius=self.temp_humidity_sensor.temperature,
                    relative_humidity_percent=self.temp_humidity_sensor.relative_humidity,
                    temperature_celsius_2=self.barometer.temperature,
                    pressure_hpa=self.barometer.pressure,
                    altitude_meters=self.barometer.altitude,
                    ambient_light_count=self.uv_light_sensor.light,
                    ambient_light_lux=self.uv_light_sensor.lux,
                    uv_count=self.uv_light_sensor.uvs,
                    uv_index=self.uv_light_sensor.uvi,
                    infrared_count=self.ir_light_sensor.infrared,
                    visible_count=self.ir_light_sensor.visible,
                    full_spectrum_count=self.ir_light_sensor.full_spectrum,
                    ir_visible_lux=self.ir_light_sensor.lux,
                    pm10_standard_ug_m3=air_quality_data[0],
                    pm25_standard_ug_m3=air_quality_data[1],
                    pm100_standard_ug_m3=air_quality_data[2],
                    pm10_environmental_ug_m3=air_quality_data[3],
                    pm25_environmental_ug_m3=air_quality_data[4],
                    pm100_environmental_ug_m3=air_quality_data[5],
                    particulate_03um_per_01L=air_quality_data[6],
                    particulate_05um_per_01L=air_quality_data[7],
                    particulate_10um_per_01L=air_quality_data[8],
                    particulate_25um_per_01L=air_quality_data[9],
                    particulate_50um_per_01L=air_quality_data[10],
                    particulate_100um_per_01L=air_quality_data[11],
                    timestamp=datetime.now(),
                )

            except Exception as e:
                logger.error(f"An unhandled exception occurred while reading data from sensors: {e}"
                             f"\n{traceback.format_exc()}")

            if data is not None:
                try:
                    self.data_log(data.encode_to_csv())
                except Exception as e:
                    logger.error(f"An unhandled exception occurred while logging data: {e}\n{traceback.format_exc()}")

                if self.count % 5 == 0:
                    # only transmit once every 5s
                    try:
                        data_header = DataHeader(
                            sender=self.get_device_id(),
                            data_type=Type.SCIENCE_DATA,
                            priority=Priority.DATA,
                        )
                        packet = Packet(data, data_header)
                        self._mqtt.send(Topic.RADIO_TRANSMIT, packet)
                    except Exception as e:
                        logger.error(f"An unhandled exception occurred while transmitting data: {e}"
                                     f"\n{traceback.format_exc()}")

            self.count += 1
            self.thread_sleep(logger, 1)

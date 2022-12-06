import logging
import time
import traceback

import Adafruit_BBIO.ADC as ADC

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class ADCDriver(DriverBase):
    ADC.setup()

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_2

    @staticmethod
    def get_device_name() -> str:
        return "ADC-Driver"

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            try:
                # uvb = ADC.read_raw("P9_39")
                uvb = ADC.read("P9_39")
                uvb_convert = uvb * 42 / 18 * 10
                uvb_str = str(round(uvb_convert, 3))
            except Exception as e:
                uvb_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get UVB data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                co2 = ADC.read_raw("P9_40")
                co2_convert = co2 * 42 / 18
                co2_str = str(round(co2_convert, 3))
            except Exception as e:
                co2_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get CO2 data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                o3_gas = ADC.read_raw("P9_37")
                o3_gas_convert = o3_gas * 42 / 18
                o3_gas_str = str(round(o3_gas_convert, 3))
            except Exception as e:
                o3_gas_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get O3 gas data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                o3_reference = ADC.read_raw("P9_38")
                o3_reference_convert = o3_reference * 42 / 18
                o3_reference_str = str(round(o3_reference_convert, 3))
            except Exception as e:
                o3_reference_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get O3 reference data"
                                f": {e}\n{traceback.format_exc()}")
            try:
                o3_temp = ADC.read_raw("P9_33")
                o3_temp_convert = o3_temp * 42 / 18
                o3_temp_str = str(round(o3_temp_convert, 3))
            except Exception as e:
                o3_temp_str = '-1'
                logger.critical("A fatal exception occurred when attempting to get O3 temperature data"
                                f": {e}\n{traceback.format_exc()}")

            csv_row1 = [uvb_str]
            csv_row2 = [co2_str]
            csv_row3 = [o3_gas_str]
            csv_row4 = [o3_reference_str]
            csv_row5 = [o3_temp_str]

            # this saves data to a file
            try:
                self.data_log(csv_row1)
                self.data_log(csv_row2)
                self.data_log(csv_row3)
                self.data_log(csv_row4)
                self.data_log(csv_row5)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                self.data_transmit(csv_row1)
                self.data_transmit(csv_row2)
                self.data_transmit(csv_row3)
                self.data_transmit(csv_row4)
                self.data_transmit(csv_row5)
            except Exception as e:
                logger.error(f"unable to transmit data: {e}")

            time.sleep(0.5)

    @staticmethod
    def enabled() -> bool:
        return True

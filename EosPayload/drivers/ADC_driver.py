import logging
import time
import traceback

import Adafruit_BBIO.ADC as ADC

from EosLib.device import Device
from EosPayload.lib.driver_base import DriverBase


class ADCDriver(DriverBase):

    def setup(self) -> None:
        super().setup()
        ADC.setup()
        time.sleep(1)

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        count = 0

        ADC.setup()
        analogPin = "P9_40"

        while True:
            potVal = ADC.read(analogPin)
            potVolt = potVal*1.8
            logger.info("RADIOACTIVITY" + potVolt)
            time.sleep(.5)

        # while True:
        #     try:
        #         uvb = ADC.read("P9_39")
        #         uvb_convert = uvb * 42 / 18

        #         # CALCULATING UVB
        #         actual_uvb = uvb_convert * 10
        #         actual_uvb_str = str(round(actual_uvb, 3))
        #     except Exception as e:
        #         actual_uvb_str = '-1'
        #         logger.critical("A fatal exception occurred when attempting to get UVB data"
        #                         f": {e}\n{traceback.format_exc()}")
        #     try:
        #         co2 = ADC.read_raw("P9_40")
        #         co2_convert = co2 * 42 / 18

        #         # CALCULATING CO2 CONCENTRATION
        #         actual_co2_concentration = pow(400, ((1500 - co2_convert) / 600))
        #         actual_co2_concentration_str = str(round(actual_co2_concentration, 3))

        #     except Exception as e:
        #         actual_co2_concentration_str = '-1'
        #         logger.critical("A fatal exception occurred when attempting to get CO2 data"
        #                         f": {e}\n{traceback.format_exc()}")
        #     try:
        #         o3_gas = ADC.read("P9_37")
        #         o3_gas_convert = o3_gas * 42 / 18
        #         o3_gas_str = str(round(o3_gas_convert, 3))

        #         o3_reference = ADC.read("P9_38")
        #         o3_reference_convert = o3_reference * 42 / 18
        #         o3_reference_str = str(round(o3_reference_convert, 3))

        #         o3_temp = ADC.read("P9_33")
        #         o3_temp_convert = o3_temp * 42 / 18
        #         o3_temp_str = str(round(o3_temp_convert, 3))

        #         # CALCULATING O3 CONCENTRATION
        #         m = 4.94 * 499 * pow(10, -6)  # sensor calibration factor: m = sensitivity code * TIA gain * 10^-6
        #         v_offset = 0  # V_offset = 0 is an adequate approximation from datasheet
        #         v_gas0 = o3_reference_convert + v_offset  # V_gas0 = V_ref + V_offset
        #         actual_o3_gas_concentration = (1 / m) * (o3_gas_convert - v_gas0)
        #         actual_o3_gas_concentration_str = str(round(actual_o3_gas_concentration, 3))
        #     except Exception as e:
        #         o3_gas_str = '-1'
        #         o3_reference_str = '-1'
        #         o3_temp_str = '-1'
        #         actual_o3_gas_concentration_str = '-1'
        #         logger.critical("A fatal exception occurred when attempting to get O3 concentration"
        #                         f": {e}\n{traceback.format_exc()}")

        #     csv_row = [actual_uvb_str, actual_co2_concentration_str, o3_gas_str,
        #                o3_reference_str, o3_temp_str, actual_o3_gas_concentration_str]

        #     # this saves data to a file
        #     try:
        #         self.data_log(csv_row)
        #     except Exception as e:
        #         logger.error(f"unable to log data: {e}")

        #     # this sends data to the radio to get relayed to the ground station
        #     if count % 2 == 0:
        #         try:
        #             self.data_transmit(csv_row)
        #             #time.sleep(1)
        #         except Exception as e:
        #             logger.error(f"unable to transmit data: {e}")
        #     count += 1
        #     time.sleep(1)


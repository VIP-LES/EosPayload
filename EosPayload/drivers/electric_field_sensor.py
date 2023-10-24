from EosPayload.lib.base_drivers.driver_base import DriverBase
import time
import logging
try:
    import Adafruit_BBIO.ADC as ADC
except ModuleNotFoundError:
    pass


class ElectricFieldSensor(DriverBase):


    def device_read(self, logger: logging.Logger) -> None:
        adc_pin = "32"
        ADC.setup()
        try:
            while True:
                # Read the voltage from the ADC pin
                value = ADC.read(adc_pin)
                voltage = value * 1.8  # BeagleBone Black has a 1.8V reference voltage
                logger.info(f"ADC Value: {value}, Voltage: {voltage:.2f} V")
                time.sleep(1)

        except Exception as e:
            logger.info(f"An error occurred: {e}")

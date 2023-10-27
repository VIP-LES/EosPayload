from EosPayload.lib.base_drivers.driver_base import DriverBase
import time
import logging
try:
    import Adafruit_BBIO.ADC as ADC
except ModuleNotFoundError:
    print("ADC not installed correctly")
    pass


class ElectricFieldSensor(DriverBase):
    def device_read(self, logger: logging.Logger) -> None:
        adc_pins = ["P9_36", "P9_38", "P9_40"]
        for pin in adc_pins:
            ADC.setup(pin)
        try:
            while True:
                # Read the voltage from the ADC pin
                values = [ADC.read(pin) for pin in adc_pins]
                voltages = [value * 1.8 for value in values]  # BeagleBone Black has a 1.8V reference voltage
                for i, pin in adc_pins:
                    logger.info(f"ADC{pin}, Voltage: {voltages[i]:.2f} V")
                time.sleep(1)

        except Exception as e:
            logger.info(f"An error occurred: {e}")

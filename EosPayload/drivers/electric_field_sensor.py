from EosPayload.lib.base_drivers.driver_base import DriverBase
import time
import logging
try:
    import Adafruit_BBIO.ADC as ADC
except ModuleNotFoundError:
    print("ADC not installed correctly")
    pass


class ElectricFieldSensor(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.pin_1 = "P9_36"
        self.pin_2 = "P9_38"
        self.pin_3 = "P9_40"
    def setup(self) -> None:
        super().setup()
        try:
            ADC
        except NameError:
            raise Exception("failed to import ADC library")

        self.register_thread('device-read', self.device_read)

        ADC.setup(self.pin_1)
        ADC.setup(self.pin_2)
        ADC.setup(self.pin_3)
    def device_read(self, logger: logging.Logger) -> None:
        adc_pins = [self.pin_1, self.pin_2, self.pin_3]
        try:
            while True:
                # Read the voltage from the ADC pin
                values = [ADC.read(pin) for pin in adc_pins]
                voltages = [value * 1.0 for value in values]
                for i, pin in enumerate(adc_pins):
                    self._logger.info(f"ADC{pin}, Voltage: {voltages[i]:.2f} V")
                self.thread_sleep(logger, 2)

        except Exception as e:
            self._logger.info(f"An error occurred: {e}")

    def cleanup(self):
        try:
            ADC.cleanup()
        except NameError:
            pass
        super(ElectricFieldSensor, self).cleanup()
        

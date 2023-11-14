from EosPayload.lib.base_drivers.driver_base import DriverBase
import time
import logging
from EosLib.format.formats.e_field import EField
from EosLib.packet.data_header import DataHeader
from EosLib.format import Type

from EosLib.packet import Packet

from EosLib.packet.definitions import Priority

from EosPayload.lib.mqtt import Topic

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
        voltages = [None, None, None]
        while True:
            try:
                # Read the voltage from the ADC pin
                values = [ADC.read(pin) for pin in adc_pins]
                voltages = [value * 1.0 for value in values]
                for i, pin in enumerate(adc_pins):
                    self._logger.info(f"ADC{pin}, Voltage: {voltages[i]:.2f} V")

            except Exception as e:
                self._logger.info(f"An error occurred while reading voltages: {e}")

            efield_obj = EField(voltages[0], voltages[1], voltages[2])

            header = DataHeader(
                data_type=Type.E_FIELD,
                sender=self.get_device_id(),
                priority=Priority.DATA
            )
            packet = Packet(
                body=efield_obj,
                data_header=header,
            )
            self._mqtt.send(Topic.RADIO_TRANSMIT, packet)

            self.thread_sleep(logger, 2)

    def cleanup(self):
        try:
            ADC.cleanup()
        except NameError:
            pass
        super(ElectricFieldSensor, self).cleanup()
        

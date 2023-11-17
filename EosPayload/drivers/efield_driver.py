import logging
import traceback


from EosLib.format.formats.e_field import EField
from EosLib.format import Type
from EosLib.packet import Packet
from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority

from EosPayload.lib.base_drivers.driver_base import DriverBase
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
                voltages[0] = ADC.read(self.pin_1)
                voltages[1] = ADC.read(self.pin_2)
                voltages[2] = ADC.read(self.pin_3)

            except Exception as e:
                self._logger.info(f"An error occurred while reading voltages: {e}\n{traceback.format_exc()}")

            try:
                row = []
                for value in voltages:
                    row.append(str(value))
                # logged as Voltage 1, Voltage 2, Voltage 3
                self.data_log(row)
            except Exception as e:
                logger.error(f"An unhandled exception occurred while logging data: {e}\n{traceback.format_exc()}")

            try:
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
            except Exception as e:
                logger.error(f"exception occurred while creating EField format: {e}\n{traceback.format_exc()}")
                self.thread_sleep(logger, 1)



    def cleanup(self):
        try:
            ADC.cleanup()
        except NameError:
            pass
        super(ElectricFieldSensor, self).cleanup()
        

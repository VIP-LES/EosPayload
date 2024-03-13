import logging
import traceback

from EosLib.format.formats.field_mill import FieldMill
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


class FieldMillSensor(DriverBase):
    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        # INSERT THE CORRECT PIN NUMBERS ONCE IMPLEMENTED
        self.pin_1 = "VOLTAGE_PIN"
        self.pin_2 = "FREQUENCY_PIN"

    def setup(self) -> None:
        super().setup()
        try:
            ADC
        except NameError:
            raise Exception("failed to import ADC library")

        self.register_thread('device-read', self.device_read)

        ADC.setup(self.pin_1)
        ADC.setup(self.pin_2)

    def device_read(self, logger: logging.Logger) -> None:
        adc_pins = [self.pin_1, self.pin_2]
        voltage = None
        frequency = None
        counter = 0
        while True:
            counter += 1
            try:
                # Read the voltage from the ADC pin
                voltage = ADC.read(self.pin_1)
                frequency = ADC.read(self.pin_2)
            except Exception as e:
                self._logger.info(f"An error occurred while reading voltages: {e}\n{traceback.format_exc()}")

            try:
                row = []
                row.append(voltage)
                row.append(frequency)
                # logged as Voltage, Frequency
                self.data_log(row)
            except Exception as e:
                logger.error(f"An unhandled exception occurred while logging data: {e}\n{traceback.format_exc()}")

            if counter % 5 == 0:
                try:
                    field_mill_obj = FieldMill(voltage, frequency)
                    header = DataHeader(
                        data_type=Type.FIELDMILL,
                        sender=self.get_device_id(),
                        priority=Priority.DATA
                    )
                    packet = Packet(
                        body=field_mill_obj,
                        data_header=header,
                    )
                    self._mqtt.send(Topic.RADIO_TRANSMIT, packet)
                except Exception as e:
                    logger.error(f"exception occurred while creating FieldMill format: {e}\n{traceback.format_exc()}")

            self.thread_sleep(logger, 1)

    def cleanup(self):
        try:
            ADC.cleanup()
        except NameError:
            pass
        super(FieldMillSensor, self).cleanup()


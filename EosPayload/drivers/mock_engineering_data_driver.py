import time

from EosLib.packet.definitions import Device

from EosPayload.drivers.engineering_data_driver import EngineeringDataDriver


class MockEngineeringDataDriver(EngineeringDataDriver):
    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_name() -> str:
        return "mock-engineering-data-driver"

    @staticmethod
    def get_device_id() -> Device:
        # This is a last minute hack because we're running out of Devices and I want to avoid patching EosLib the day
        # prior to launch
        return Device.MISC_CAMERA_1

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.data_file_path = "EosPayload/mock_esp_data.csv"
        self.data_file = None

    def setup(self) -> None:
        super(EngineeringDataDriver, self).setup()
        self.data_file = open(self.data_file_path, 'r')

    def fetch_data(self) -> str:
        time.sleep(0.01)
        return ','.join(self.data_file.readline().strip().replace('\x00', '').split(',')[:-1])

    def is_alive(self):
        return True

    def cleanup(self):
        self.data_file.close()

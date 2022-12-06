import time

from EosLib.packet.definitions import Device

from EosPayload.drivers.engineering_data_driver import EngineeringDataDriver


class MockEngineeringDataDriver(EngineeringDataDriver):
    # TODO: Move everything out of init
    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.data_file_path = "mock_esp_data.csv"
        self.data_file = None

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_name() -> str:
        return "mock-engineering-data-driver"

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_1

    def setup(self) -> None:
        self.data_file = open(self.data_file_path, 'r')

    def fetch_data(self) -> str:
        time.sleep(0.01)
        return ','.join(self.data_file.readline().strip().replace('\x00', '').split(',')[:-1])

    def is_alive(self):
        return True

    def cleanup(self):
        self.data_file.close()

import time

from EosLib.device import Device

from EosPayload.drivers.engineering_data_driver import EngineeringDataDriver


class MockEngineeringDataDriver(EngineeringDataDriver):


    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
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

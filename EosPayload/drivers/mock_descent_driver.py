import time

from EosLib.device import Device
from EosLib.format.position import FlightState

from EosPayload.drivers.engineering_data_driver import EngineeringDataDriver


class MockDescentDriver(EngineeringDataDriver):
    """
    Fakes a descent at constant speed of 100 ft/second, which should take about 6 minutes in total
    """
    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.current_altitude = 20000.0

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_name() -> str:
        return "mock-descent-driver"

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_SENSOR_4

    def setup(self) -> None:
        super(EngineeringDataDriver, self).setup()

    def fetch_data(self) -> str:
        time.sleep(1)
        dummy_data = f"16:48:03,9/4,3404.4717N,8353.9922W,10.34,{self.current_altitude},10,-0.89,-1.01,9.66," \
                     f"-0.17,0.10,0.34,8.57,4026.39,7.80,13.25, 37.932\n"
        mock_data = ','.join(dummy_data.strip().replace('\x00', '').split(',')[:-1])
        self.current_altitude = self.current_altitude - 100 if self.current_altitude >= 100 else 0
        self.current_flight_state = FlightState.DESCENT
        return mock_data

    def is_alive(self):
        return True

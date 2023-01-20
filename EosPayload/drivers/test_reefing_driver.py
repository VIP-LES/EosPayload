import logging

from EosLib.packet.definitions import Device

from EosPayload.drivers.reefing_driver import ReefingDriver


class TestReefingDriver(ReefingDriver):
    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        # This is a last minute hack because we're running out of Devices and I want to avoid patching EosLib the day
        # prior to launch
        return Device.MISC_CAMERA_2

    @staticmethod
    def get_device_name() -> str:
        return "test-reefing-motor-driver"

    def setup(self) -> None:
        super(ReefingDriver, self).setup()
        self.current_reef_amount = 0

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.update_interval = 5

    def set_reefing_level(self, reefing_percent: float, logger: logging.Logger):
        logger.info(f"Setting reefing to {reefing_percent}%")
        logger.info(f"Current altitude: {self.latest_position.altitude}, "
                    f"state: {self.latest_position.flight_state.name}")


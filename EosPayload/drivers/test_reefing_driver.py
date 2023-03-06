import logging

from EosLib.packet.definitions import Device

from EosPayload.drivers.reefing_driver import ReefingDriver


class TestReefingDriver(ReefingDriver):

    def setup(self) -> None:
        super(ReefingDriver, self).setup()
        self.current_reef_amount = 0

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.update_interval = 5

    def set_reefing_level(self, reefing_percent: float, logger: logging.Logger):
        logger.info(f"Setting reefing to {reefing_percent}%")
        logger.info(f"Current altitude: {self.latest_position.altitude}, "
                    f"state: {self.latest_position.flight_state.name}")


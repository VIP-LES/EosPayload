import time
import logging

from EosLib.format.position import Position, FlightState
from EosLib.device import Device

from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase


class TestPositionAwareDriver(PositionAwareDriverBase):
    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_2

    @staticmethod
    def get_device_name() -> str:
        return "test-position-aware-driver"

    def device_command(self, logger: logging.Logger) -> None:
        old_position = Position()
        while True:
            time.sleep(1)
            if old_position.timestamp != self.latest_position.timestamp:
                flight_state_str = FlightState(self.latest_position.flight_state).name
                logger.info("New position found at {}. "
                            "Flight state: {}".format(self.latest_position.timestamp.isoformat(),
                                                      flight_state_str))
                old_position = self.latest_position

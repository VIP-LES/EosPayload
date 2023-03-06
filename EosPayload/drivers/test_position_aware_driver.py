import time
import logging

from EosLib.format.position import Position, FlightState
from EosLib.packet.definitions import Device

from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase


class TestPositionAwareDriver(PositionAwareDriverBase):

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

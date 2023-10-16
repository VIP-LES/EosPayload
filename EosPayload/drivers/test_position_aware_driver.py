import logging

from EosLib.format.formats.position import Position, FlightState

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class TestPositionAwareDriver(PositionAwareDriverBase):

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-command', self.device_command)

    def device_command(self, logger: logging.Logger) -> None:
        old_position = Position(None, 0, 0, 0, 0, 0)
        while True:
            self.thread_sleep(logger, 1)
            if old_position.gps_time != self.latest_position.gps_time:
                flight_state_str = FlightState(self.latest_position.flight_state).name
                logger.info("New position found at {}. "
                            "Flight state: {}".format(self.latest_position.gps_time.isoformat(),
                                                      flight_state_str))
                old_position = self.latest_position

import logging

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class PositionAwareLoggingDriver(PositionAwareDriverBase):

    def setup(self) -> None:
        super().setup()
        self.register_thread('position-logging', self.device_command)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            self.thread_sleep(logger, 10)
            try:
                if self.latest_position is not None:
                    self.data_log([str(self.latest_position.timestamp),
                                   str(self.latest_position.latitude),
                                   str(self.latest_position.longitude),
                                   str(self.latest_position.altitude),
                                   str(self.latest_position.speed),
                                   str(self.latest_position.number_of_satellites),
                                   str(self.latest_position.valid),
                                   str(self.latest_position.flight_state.name)])
                else:
                    self.data_log(["no position"])
            except Exception as e:
                logger.error(f"Encountered error trying to log: {e}")
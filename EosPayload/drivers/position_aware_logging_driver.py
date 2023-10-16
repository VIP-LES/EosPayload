import logging
import traceback

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class PositionAwareLoggingDriver(PositionAwareDriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.callback_logger = logging.getLogger(f"{self._pretty_id}.position-callback")

    def position_callback(self, _client, _userdata, _message):
        super().position_callback(_client, _userdata, _message)
        try:
            if self.latest_position is not None:
                self.data_log([str(self.latest_position.gps_time.isoformat()),
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
            self.callback_logger.error(f"Error occurred while attempting to log latest position: {e}"
                                       f"\n{traceback.format_exc()}")

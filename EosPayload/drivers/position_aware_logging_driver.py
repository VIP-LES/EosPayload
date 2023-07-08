import logging

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class PositionAwareLoggingDriver(PositionAwareDriverBase):

    def position_callback(self, _client, _userdata, _message):
        super().position_callback(_client, _userdata, _message)
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

import logging
import time

import Adafruit_BBIO.PWM as PWM

from EosLib.format.position import FlightState
from EosLib.packet.definitions import Device

from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase


class ReefingDriver(PositionAwareDriverBase):
    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def command_thread_enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.REEFING_MOTOR

    @staticmethod
    def get_device_name() -> str:
        return "reefing-motor-driver"

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.pwm_pin = "P9_14"
        self.current_reef_amount = 0
        self.old_position = None
        self.update_interval = 30

    def setup(self) -> None:
        super().setup()
        PWM.start(self.pwm_pin, 0)
        self.current_reef_amount = 0

    def set_reefing_level(self, reefing_percent: float, logger: logging.Logger):
        if reefing_percent != self.current_reef_amount:
            logger.info(f"Setting reefing to {reefing_percent}%")
            PWM.set_duty_cycle(self.pwm_pin, reefing_percent)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            if self.latest_position != self.old_position and self.latest_position.flight_state == FlightState.DESCENT:
                if self.latest_position.altitude > 30000:
                    self.set_reefing_level(0, logger)
                elif self.latest_position.altitude > 28000:
                    self.set_reefing_level(55, logger)
                elif self.latest_position.altitude > 26000:
                    self.set_reefing_level(75, logger)
                elif self.latest_position.altitude > 24000:
                    self.set_reefing_level(90, logger)
                elif self.latest_position.altitude > 8000:
                    self.set_reefing_level(75, logger)
                elif self.latest_position.altitude > 6000:
                    self.set_reefing_level(55, logger)
                else:
                    self.set_reefing_level(0, logger)
            else:
                self.set_reefing_level(0, logger)

            # This check/update ensures that a crash somewhere that prevents position updates will cause a full dis-reef
            self.old_position = self.latest_position
            time.sleep(self.update_interval)

import logging

try:
    import Adafruit_BBIO.PWM as PWM
except ModuleNotFoundError:
    pass

from EosLib.format.formats.position import FlightState

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase


class ReefingDriver(PositionAwareDriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.pwm_pin = "P9_14"
        self.current_reef_amount = 0
        self.old_position = None
        self.update_interval = 3
        self.reefing_stages = {
            0: 0,   # slack
            1: 27,  # taut
            2: 45,  # max drag
            3: 64,  # mid reef
            4: 82   # max reef
        }

    def setup(self) -> None:
        super().setup()

        try:
            PWM
        except NameError:
            raise Exception("failed to import PWM library")

        self.register_thread('device-command', self.device_command)

        PWM.start(self.pwm_pin, 0)
        self.current_reef_amount = 0

    def set_reefing_level(self, reefing_stage: int, logger: logging.Logger):
        reefing_percent = self.reefing_stages[reefing_stage]
        if reefing_percent != self.current_reef_amount:
            logger.info(f"Setting reefing to {reefing_percent}%")
            PWM.set_duty_cycle(self.pwm_pin, reefing_percent)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            if self.latest_position != self.old_position and self.latest_position.flight_state == FlightState.DESCENT:
                if self.latest_position.altitude > 16000:
                    self.set_reefing_level(1, logger)
                elif self.latest_position.altitude > 14000:
                    self.set_reefing_level(2, logger)
                elif self.latest_position.altitude > 12000:
                    self.set_reefing_level(3, logger)
                elif self.latest_position.altitude > 10000:
                    self.set_reefing_level(4, logger)
                elif self.latest_position.altitude > 8000:
                    self.set_reefing_level(3, logger)
                elif self.latest_position.altitude > 6000:
                    self.set_reefing_level(2, logger)
                else:
                    self.set_reefing_level(2, logger)
            else:
                self.set_reefing_level(0, logger)

            # This check/update ensures that a crash somewhere that prevents position updates will cause a full dis-reef
            self.old_position = self.latest_position
            self.thread_sleep(logger, self.update_interval)

    def cleanup(self):
        self.set_reefing_level(0, self._logger)
        PWM.stop("P9_14")
        PWM.cleanup()
        super().cleanup()

        '''

            
            STAGE -> Voltage -> %PWM
            0 -> 0V -> 0%
            1 -> .9V -> %27
            2 -> 1.5V -> 45%
            3 -> 2.1V -> 64%
            4 -> 2.7V -> 82%
            
        '''

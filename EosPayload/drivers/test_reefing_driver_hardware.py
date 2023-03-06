import logging
import random
import time

from EosLib.packet.definitions import Device

from EosPayload.drivers.reefing_driver import ReefingDriver


class TestReefingDriverHardware(ReefingDriver):

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            reef_level = random.randrange(0, 100)
            self.set_reefing_level(reef_level, logger)
            time.sleep(30)

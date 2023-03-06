import logging
import time

from EosLib.packet.definitions import Device
from EosPayload.drivers.test_driver import TestDriver

# this example shows how you can extend other drivers you've already made
# so you can avoid duplicate code


class TestDriver2(TestDriver):
    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    @staticmethod
    def get_required_device_config() -> list[str]:
        return ["print_text"]

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            print(self._driver_settings.get("print_text"))
            time.sleep(5)


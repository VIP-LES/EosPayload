import logging
import time

from EosPayload.drivers.test_driver import TestDriver

# this example shows how you can pass custom config fields into a driver

class TestConfigDriver(TestDriver):
    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    @staticmethod
    def get_required_config_fields() -> list[str]:
        return ["print_text"]

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            print(self._settings.get("print_text"))
            time.sleep(5)


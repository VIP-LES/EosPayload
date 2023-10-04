import logging

from EosPayload.drivers.test_driver import TestDriver

# this example shows how you can pass custom config fields into a driver


class TestConfigDriver(TestDriver):

    @staticmethod
    def get_required_config_fields() -> list[str]:
        return ["print_text"]

    def device_read(self, logger: logging.Logger) -> None:
        while True:
            self.check_stop_signal(logger)
            print(self._settings.get("print_text"))
            self.thread_sleep(logger, 5)

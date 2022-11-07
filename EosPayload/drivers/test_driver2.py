from EosPayload.drivers.test_driver import TestDriver


class TestDriver2(TestDriver):

    @staticmethod
    def get_device_id() -> str:
        return "test-driver-002"

    def enabled(self) -> bool:
        return False
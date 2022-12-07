from EosLib.packet.definitions import Device
from EosPayload.drivers.test_driver import TestDriver

# this example shows how you can extend other drivers you've already made
# so you can avoid duplicate code


class TestDriver2(TestDriver):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_TEST_2

    # disabling this driver for now
    @staticmethod
    def enabled() -> bool:
        return False

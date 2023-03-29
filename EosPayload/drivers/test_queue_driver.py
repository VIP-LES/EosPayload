from datetime import datetime
from queue import PriorityQueue
from random import randint
import logging
import time

from EosLib.device import Device
from EosPayload.lib.driver_base import DriverBase


class TestQueueDriver(DriverBase):

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_TEST_3

    @staticmethod
    def get_device_name() -> str:
        return "test-queue-driver"

    @staticmethod
    def enabled() -> bool:
        return False

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self._thread_queue = PriorityQueue()

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:

        counter = 0
        while True:
            for priority in [randint(0, 10) for _i in range(0, 10)]:
                # counter is the data.  the random number and the timestamp are used to define priority order for the q
                self._thread_queue.put((priority, datetime.now(), counter,))
                counter = counter + 1
                time.sleep(0.001)

            time.sleep(10)

    @staticmethod
    def command_thread_enabled() -> bool:
        return True

    def device_command(self, logger: logging.Logger) -> None:

        while True:
            (priority, timestamp, value) = self._thread_queue.get()
            logger.info(f"popped item #{value} (priority = {priority}, timestamp = {timestamp})")
            time.sleep(0.1)

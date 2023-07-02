from datetime import datetime
from queue import PriorityQueue
from random import randint
import logging
import time

from EosPayload.lib.base_drivers.driver_base import DriverBase


class TestQueueDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self._thread_queue = PriorityQueue()

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-read', self.device_read)
        self.register_thread('device-command', self.device_command)

    def device_read(self, logger: logging.Logger) -> None:
        counter = 0
        while True:
            for priority in [randint(0, 10) for _i in range(0, 10)]:
                # counter is the data.  the random number and the timestamp are used to define priority order for the q
                self._thread_queue.put((priority, datetime.now(), counter,))
                counter = counter + 1
                time.sleep(0.001)

            self.thread_sleep(logger, 10)

    def device_command(self, logger: logging.Logger) -> None:
        while True:
            (priority, timestamp, value) = self._thread_queue.get()
            logger.info(f"popped item #{value} (priority = {priority}, timestamp = {timestamp})")
            self.thread_sleep(logger, 0.1)

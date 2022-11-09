from datetime import datetime
from queue import Queue, PriorityQueue
from random import randint
import logging
import time

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase


class TestQueueDriver(DriverBase):

    _thread_queue = PriorityQueue()

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_3

    @staticmethod
    def get_device_name() -> str:
        return "test-queue-driver"

    def device_read(self, logger: logging.Logger, shared_queue: Queue) -> None:

        counter = 0
        while True:
            for priority in [randint(0, 10) for _i in range(0, 10)]:
                # counter is the data.  the random number and the timestamp are used to define priority order for the q
                shared_queue.put((priority, datetime.now(), counter,))
                counter = counter + 1
                time.sleep(0.001)

            time.sleep(10)

    def device_command(self, logger: logging.Logger, shared_queue: Queue) -> None:

        while True:
            (priority, timestamp, value) = shared_queue.get()
            logger.info(f"popped item #{value} (priority = {priority}, timestamp = {timestamp})")
            time.sleep(0.1)

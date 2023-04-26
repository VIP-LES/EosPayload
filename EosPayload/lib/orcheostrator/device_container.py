from datetime import datetime
from enum import Enum, unique
from multiprocessing import Process

from EosLib import Device

from EosPayload.lib.driver_base import DriverBase


@unique
class Status(Enum):
    NONE = 0
    INVALID = 1
    HEALTHY = 2
    UNHEALTHY = 3
    TERMINATED = 4
    INITIALIZED = 5


class StatusUpdate:
    def __init__(self, driver_id: int, status: Status, thread_count: int, reporter: Device, effective: datetime):
        self.driver_id = driver_id
        self.status = status
        self.thread_count = thread_count
        self.reporter = reporter
        self.effective = effective


class DeviceContainer:

    def __init__(self, driver: DriverBase, process: Process = None, config: dict = None):
        self.driver = driver
        self.process = process
        self.config = config
        self.status = Status.NONE
        self.thread_count = 0
        self.status_reporter = Device.NO_DEVICE
        self.status_since = datetime.now()

    def update_status(self, status: Status, thread_count: int = 0, reporter: Device = Device.ORCHEOSTRATOR,
                      effective: datetime = None):
        if effective is None:
            effective = datetime.now()

        if effective >= self.status_since:
            self.status = status
            self.thread_count = thread_count
            self.status_reporter = reporter
            self.status_since = effective

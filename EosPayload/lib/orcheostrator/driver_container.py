from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from multiprocessing import Process

from EosLib import Device

from EosPayload.lib.driver_base import DriverBase


@unique
class Status(Enum):
    NONE = 0
    INVALID = 1
    DISABLED = 2
    HEALTHY = 3
    UNHEALTHY = 4
    TERMINATED = 5


@dataclass
class StatusUpdate:
    driver_id: Device = None
    status: Status = None
    thread_count: int = None
    reporter: Device = None
    effective: datetime = None

    def update(self, other):
        if other.effective is not None and other.effective >= self.effective:
            if other.driver_id is not None:
                self.driver_id = other.driver_id
            if other.status is not None:
                self.status = other.status
            if other.thread_count is not None:
                self.thread_count = other.thread_count
            if other.reporter is not None:
                self.reporter = other.reporter


class DriverContainer:

    def __init__(self, driver: DriverBase, process: Process = None):
        self.driver = driver
        self.process = process
        self.status = StatusUpdate(
            status=Status.NONE,
            thread_count=0,
            reporter=Device.NO_DEVICE,
            effective=datetime.now()
        )

    def update_status(self, status_update: StatusUpdate = None, status: Status = None, thread_count: int = None,
                      reporter: Device = Device.ORCHEOSTRATOR, effective: datetime = None):
        if status_update is None:
            if effective is None:
                effective = datetime.now()
            status_update = StatusUpdate(status=status, thread_count=thread_count,
                                         reporter=reporter, effective=effective)

        self.status.update(status_update)

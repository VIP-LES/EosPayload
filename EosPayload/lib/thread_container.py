from dataclasses import dataclass
from threading import Thread

from EosLib.format.formats.health.driver_health_report import ThreadStatus


@dataclass
class ThreadContainer:
    name: str
    thread: Thread | None
    status: ThreadStatus

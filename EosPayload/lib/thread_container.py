import threading
from dataclasses import dataclass
from enum import Enum, unique
from threading import Thread


@unique
class ThreadStatus(Enum):
    NONE = 0
    INVALID = 1
    REGISTERED = 2
    ALIVE = 3
    DEAD = 4


@dataclass
class ThreadContainer:
    name: str
    thread: Thread | None
    status: ThreadStatus

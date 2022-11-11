import itertools
import heapq
from datetime import datetime
import logging
import time

#from EosLib.packet.definitions import Device
#from EosPayload.lib.driver_base import DriverBase


pq = []                         # list of entries arranged in a heap
counter = itertools.count()     # unique sequence count



def add_packet(priority, packet):
    'Add a new task or update the priority of an existing task'
    entry = [priority, datetime.now(), packet]
    heapq.heappush(pq, entry)


def pop_packet():
    'Remove and return the lowest priority task. Raise KeyError if empty.'
    if len(pq) != 0:
        priority, time, packet = heapq.heappop(pq)
        return packet
    else:
        raise KeyError('pop from an empty priority queue')






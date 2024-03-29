from enum import Enum, unique

MQTT_HOST = 'localhost'


# MQTT Constants
@unique
class QOS(int, Enum):
    DELIVER_NO_ACK = 0
    DELIVER_AT_LEAST_ONCE = 1
    DELIVER_AT_MOST_ONCE = 2


# Config-ish constants
@unique
class Topic(str, Enum):
    RADIO_TRANSMIT = 'radio/transmit'
    HEALTH_HEARTBEAT = 'health/heartbeat'
    POSITION_UPDATE = 'position/update'
    PING_COMMAND = 'ping/command'
    CUTDOWN_COMMAND = 'cutdown/command'
    VALVE_COMMAND = 'valve/command'
    # register new topics by appending them to the above list

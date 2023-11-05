import argparse
import json
import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from EosLib.packet.data_header import DataHeader
from EosLib.packet.packet import Packet
from EosLib.packet.transmit_header import TransmitHeader
from EosPayload.lib.mqtt import MQTT_HOST, Topic
from EosPayload.lib.mqtt.client import Client

from EosLib.format.formats.ping_format import Ping

# example usage:
# python scripts/mqtt_pub_packet.py -t "ping/command" -b "PING 420" -d "{\"priority\":2, \"sender\":12, \"destination\":19, \"data_type\":2}" -r "{\"send_seq_num\":42}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--topic', required=True)
    parser.add_argument('-b', '--body', required=True)
    parser.add_argument('-d', '--data-header', required=False)
    parser.add_argument('-r', '--transmit-header', required=False)
    args = parser.parse_args()

    if not isinstance(args.topic, str) or args.topic not in [t.value for t in Topic]:
        raise Exception("topic must be a str in Topic enum")
    topic = Topic(args.topic)

    if not isinstance(args.body, str):
        raise Exception("body must be a str")
    # body = bytes(args.body, 'utf8')
    body = Ping(True, 120)

    if args.data_header is not None and not isinstance(args.data_header, str):
        raise Exception("data header must be dict json string or None")
    data_header = None if not args.data_header else DataHeader(**json.loads(args.data_header))

    if args.transmit_header is not None and not isinstance(args.transmit_header, str):
        raise Exception("transmit header must be dict json string or None")
    transmit_header = None if not args.transmit_header else TransmitHeader(**json.loads(args.transmit_header))

    packet = Packet(body, data_header, transmit_header)

    mqtt = Client(MQTT_HOST)
    print("sending...")
    mqtt.send(topic, packet)
    time.sleep(3)  # give packet time to send
    print("done")

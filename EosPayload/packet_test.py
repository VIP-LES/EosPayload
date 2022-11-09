import datetime

import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header

from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress

sequence_number = 2


def create_packet(data):
    created_packet = EosLib.packet.packet.Packet()
    created_packet.data_header = EosLib.packet.packet.DataHeader()

    created_packet.data_header.data_type = EosLib.packet.definitions.PacketType.TELEMETRY
    created_packet.data_header.priority = EosLib.packet.definitions.PacketPriority.DATA
    created_packet.data_header.sender = EosLib.packet.definitions.PacketDevice.GPS
    created_packet.data_header.generate_time = datetime.datetime.now()

    created_packet.body = str(data)
    created_packet.body = created_packet.body.encode()

    return created_packet


def transmit(sending_packet: EosLib.packet.packet.Packet):
    global sequence_number

    priority = sending_packet.data_header.priority

    new_transmit_header = EosLib.packet.transmit_header.TransmitHeader(sequence_number)
    sequence_number = (sequence_number + 1) % 256  # sequence number can't exceed 255, this makes sure that we don't
    sending_packet.transmit_header = new_transmit_header

    device = XBeeDevice("COM5", 9600)
    device.open()
    #xbee_net = device.get_network()
    #remote = xbee_net.discover_device("LES-PAYLOAD")
    remote = RemoteXBeeDevice(device, XBee64BitAddress.from_hex_string("13A20041CB89EE"))

    str_sending_packet = EosLib.packet.packet.Packet.encode_to_string(sending_packet)

    device.send_data_async(remote, str_sending_packet)

if __name__ == "__main__":
    packet = create_packet("All these lines of code to send a string?!")
    transmit(packet)

'''
def receive(receiving_packet: EosLib.packet.packet.Packet):
    seq_num = receiving_packet.transmit_header.send_seq_num
    print(seq_num)

    packet_body = receiving_packet.body.decode()
    print(packet_body)
'''

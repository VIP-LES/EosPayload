import datetime

import EosLib.packet.definitions
import EosLib.packet.packet
import EosLib.packet.transmit_header

sequence_number = 2


def create_packet(data):
    created_packet = EosLib.packet.packet.Packet()
    created_packet.data_header = EosLib.packet.packet.DataHeader()

    created_packet.data_header.data_type = EosLib.packet.definitions.Type.TELEMETRY
    created_packet.data_header.priority = EosLib.packet.definitions.Priority.DATA
    created_packet.data_header.sender = EosLib.packet.definitions.Device.GPS
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


def receive(receiving_packet: EosLib.packet.packet.Packet):
    seq_num = receiving_packet.transmit_header.send_seq_num
    print(seq_num)

    packet_body = receiving_packet.body.decode()
    print(packet_body)


if __name__ == "__main__":
    packet = create_packet("All these lines of code to send a string?!")
    transmit(packet)
    receive(packet)

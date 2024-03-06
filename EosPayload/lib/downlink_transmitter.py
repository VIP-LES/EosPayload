from __future__ import annotations

import math
import os
import queue
import struct

from typing import BinaryIO

from EosLib.format.formats.downlink_header_format import DownlinkCommandFormat, DownlinkCommand
from EosLib.format.formats.downlink_chunk_format import DownlinkChunkFormat

from EosLib.packet import Packet


class DownlinkTransmitter:
    def __init__(self, downlink_file: BinaryIO, file_id: int):
        self.downlink_file = downlink_file

        self.file_id = file_id
    # find size of file
        self.downlink_file.seek(0, os.SEEK_END)
        self.downlink_file_size = downlink_file.tell()
        self.downlink_file.seek(0)
    # split the file into chunks based on max chunk file
        self.chunk_size = Packet.radio_body_max_bytes - struct.calcsize(DownlinkChunkFormat.chunk_header_format_string)
        self.num_chunks = int(math.ceil(self.downlink_file_size / self.chunk_size))
        self.chunk_queue = queue.SimpleQueue()

        self.unacknowledged_chunks = set(range(self.num_chunks))
    # add chunks to queue
        for i in range(0, self.num_chunks):
            self.chunk_queue.put(i)

    def get_downlink_header(self, command_type: DownlinkCommand) -> DownlinkCommandFormat:
        # Generate and return a DownlinkCommandFormat for the downlink header
        return DownlinkCommandFormat(self.file_id, self.num_chunks, command_type)

    def get_chunk(self, chunk_num: int) -> DownlinkChunkFormat:
        # Read and return a specific chunk from the downlink_file
        self.downlink_file.seek(chunk_num * self.chunk_size)
        chunk_body = self.downlink_file.read(self.chunk_size)
        return DownlinkChunkFormat(chunk_num, chunk_body)

    def get_next_chunk(self) -> DownlinkChunkFormat | None:
        # Get the next chunk from the queue
        if self.chunk_queue.empty():
            return None

        # Skip acknowledged chunks and move to the next one
        chunk_num = self.chunk_queue.get()
        if chunk_num not in self.unacknowledged_chunks:
            return self.get_next_chunk()
        return self.get_chunk(chunk_num)

    def add_ack(self, ack: DownlinkCommandFormat) -> bool:
        # Check if the received acknowledgment matches the transmitter's info, if so set ack
        if ack.file_id == self.file_id and\
                ack.num_chunks == self.num_chunks and\
                ack.command_type == DownlinkCommand.START_ACKNOWLEDGEMENT:
            # Find missing chunks (gives an empty set if none)
            if ack.missing_chunks:
                received_chunks = set(range(self.num_chunks)).difference_update(ack.missing_chunks)
                self.unacknowledged_chunks.difference_update(received_chunks)
            return True
        else:
            return False

    def retransmit_chunks(self, missing_chunks):
        for chunk_num in missing_chunks:
            self.chunk_queue.put(chunk_num)
            self.unacknowledged_chunks.add(chunk_num)

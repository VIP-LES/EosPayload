import io
import logging
import tarfile
import traceback

from EosLib.format import Type

from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority
from EosLib.packet.packet import Packet

from EosLib.device import Device

from EosLib.format.formats.downlink_header_format import DownlinkCommandFormat, DownlinkCommand
from EosLib.format.formats.downlink_chunk_format import DownlinkChunkFormat

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic

from EosPayload.lib.downlink_transmitter import DownlinkTransmitter


class DownlinkDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
        self.transmitter = None
        self.downlink_file = None

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-command', self.device_command)

    def device_command(self, logger: logging.Logger) -> None:
        if self._mqtt:
            self._mqtt.user_data_set({'logger': logger})
            self._mqtt.register_subscriber(Topic.DOWNLINK_COMMAND, self.downlink_packet)
        while True:
            self.thread_sleep(logger, 20)

    def downlink_packet(self, client, user_data, message):
        try:
            try:
                packet = Packet.decode(message.payload)

            except Exception as e:
                user_data['logger'].error("failed to decode packet sent to "
                                          f"{Topic.DOWNLINK_COMMAND.value}: {e}")
                return

            decoded_packet = DownlinkCommandFormat.decode(packet.body.encode())
            command_type = decoded_packet.command_type

            # pass packet to correct function based on the command type
            if command_type is DownlinkCommand.START_REQUEST:
                # send START_ACK packet back with num_chunks
                self.start_ack(user_data['logger'])
            elif command_type is DownlinkCommand.START_ACK:
                # start transmission of all chunks to ground station
                self.transmit_chunks(user_data['logger'])
            elif command_type is DownlinkCommand.RETRANSMIT_MISSING_CHUNKS:
                if decoded_packet.missing_chunks:
                    # transmit only the missing chunk numbers given in packet
                    self.transmitter.add_ack(decoded_packet)
                    self.transmit_chunks(user_data['logger'])
                else:
                    # TODO print error for invalid command type, and send ERROR packet
                    pass
            elif command_type is DownlinkCommand.STOP_TRANSMISSION:
                # send STOP_TRANSMISSION packet, ending downlink
                self.stop_transmission(user_data['logger'])
            else:
                pass
                # TODO print error for invalid command type, and send ERROR packet
        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing ping_reply: {e}"
                                      f"\n{traceback.format_exc()}")

    def start_ack(self, logger: logging.Logger) -> None:
        # Define the name of the TAR archive
        archive_name = "EosPayload.tar.gz"

        # Define the path to the directory you want to archive
        directory_path = "./"

        # Create a gzipped TAR archive
        with tarfile.open(archive_name, "w:gz") as tar:
            # Add all files and directories under the specified directory
            tar.add(directory_path, arcname="")

        logger.info(f'tar file "{archive_name}" created')

        self.downlink_file = io.open(archive_name, "rb")
        self.transmitter = DownlinkTransmitter(self.downlink_file, 69)

        logger.info(f'transmitter created with {self.transmitter.num_chunks} chunks')

        # create START_ACK packet
        data_header = DataHeader(
            data_type=Type.DOWNLINK_COMMAND,
            sender=self.get_device_id(),
            priority=Priority.DATA,
        )
        downlink_header = self.transmitter.get_downlink_header(DownlinkCommand.START_ACK)
        downlink_packet = Packet(downlink_header, data_header)

        if self._mqtt:
            logger.info('sending START_ACK packet for downlink')
            self._mqtt.send(Topic.RADIO_TRANSMIT, downlink_packet)

    def transmit_chunks(self, logger: logging.Logger) -> None:
        # loops through all the chunks
        while (cur_chunk := self.transmitter.get_next_chunk()) is not None:
            # send chunk to ground station
            data_header = DataHeader(
                data_type=Type.DOWNLINK_CHUNK,
                sender=self.get_device_id(),
                priority=Priority.DATA,
            )
            downlink_packet = Packet(cur_chunk, data_header)

            if self._mqtt:
                logger.info(f'sending chunk {cur_chunk.chunk_num}')
                self._mqtt.send(Topic.RADIO_TRANSMIT, downlink_packet)

    def stop_transmission(self, logger: logging.Logger):
        # create STOP_TRANSMISSION packet
        data_header = DataHeader(
            data_type=Type.DOWNLINK_COMMAND,
            sender=self.get_device_id(),
            priority=Priority.DATA,
        )
        downlink_header = self.transmitter.get_downlink_header(DownlinkCommand.STOP_TRANSMISSION)
        downlink_packet = Packet(downlink_header, data_header)

        if self._mqtt:
            logger.info('sending STOP_TRANSMISSION packet for downlink')
            self._mqtt.send(Topic.RADIO_TRANSMIT, downlink_packet)

    def cleanup(self):
        if self.downlink_file:
            self.downlink_file.close()
        super().cleanup()

    # def transmit_data(self, logger: logging.Logger):
    #
    #         receiver = DownlinkReceiver(downlink_packet, transmitter.get_downlink_header(), png_dir)
    #
    #         def receive_chunks():
    #             # loops through all the chunks
    #             while (cur_chunk := transmitter.get_next_chunk()) is not None:
    #                 # print(cur_chunk.chunk_body)
    #
    #                 # Simulate packet drops
    #                 if random.random() >= 0.3:
    #                     receiver.write_chunk(cur_chunk)
    #                 else:
    #                     # print(f"Chunk {cur_chunk.chunk_num} has been dropped")
    #                     pass
    #
    #         # Get chunks for first time
    #         receive_chunks()
    #
    #         # Get ack packet containing missing chunks from receiver
    #         ack_packet = receiver.get_ack()
    #
    #         # If there are missing chunks in the ACK, retransmit them
    #         num_retransmits, max_transmits = 0, 10
    #         while ack_packet.missing_chunks and num_retransmits < max_transmits:
    #             print(f"Missing chunks: {ack_packet.missing_chunks}")
    #             transmitter.retransmit_chunks(ack_packet.missing_chunks)
    #             receive_chunks()
    #             time.sleep(0.1)
    #             ack_packet = receiver.get_ack()
    #             num_retransmits += 1
    #             print(f"Number of retransmission attempts: {num_retransmits}")
    #
    #         if ack_packet.missing_chunks:
    #             print(f"Missing chunks {ack_packet.missing_chunks}, image is corrupted :/")
    #
    #         # print(f"Received Chunks: {receiver.received_chunks}")

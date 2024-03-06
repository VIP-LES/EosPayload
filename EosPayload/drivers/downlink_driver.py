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
                #TODO start transmission of all chunks to ground station
                pass
            elif command_type is DownlinkCommand.RETRANSMIT_MISSING_CHUNKS:
                if decoded_packet.missing_chunks:
                    #TODO transmit only the chunk numbers given in packet
                    pass
                else:
                    #TODO send STOP_TRANSMISSION packet, ending downlink
                    pass
            else:
                pass
                #TODO print error for invalid command type, and send ERROR packet
        #
        #     if command:
        #         user_data['logger'].info(f"received PING command from device '{packet.data_header.sender}'"
        #                                  f" with sequence number '{seq_num}'")
        #
        #         response_header = DataHeader(
        #             data_type=Type.PING,
        #             sender=self.get_device_id(),
        #             priority=Priority.TELEMETRY,
        #             destination=packet.data_header.sender
        #         )
        #
        #         response = Packet(Ping(PingEnum.ACK, seq_num), response_header)
        #         client.send(Topic.RADIO_TRANSMIT, response)
        #
        #     else:
        #         user_data['logger'].info(f"received ACK for ping from device '{packet.data_header.sender}'"
        #                                  f" with sequence number '{seq_num}'")
        #
        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing ping_reply: {e}"
                                      f"\n{traceback.format_exc()}")

    def start_ack(self, logger: logging.Logger):
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

    def transmit_chunks(self):
        pass

    def cleanup(self):

        super().cleanup()

    # def transmit_data(self, logger: logging.Logger):
    #
    #         # send packet to receiver in ground station
    #         send_to_receiver(downlink_packet)
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

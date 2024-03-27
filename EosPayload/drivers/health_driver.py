import logging
import traceback
from queue import Queue

from EosLib.format import Type
from EosLib.packet import Packet
from EosLib.packet.data_header import DataHeader
from EosLib.packet.definitions import Priority
from EosLib.format.formats.health.driver_health_report import DriverHealthReport
from EosLib.format.formats.health.health_query import HealthQuery
from EosLib.format.formats.health.health_response import HealthResponse

from EosPayload.lib.base_drivers.driver_base import DriverBase
from EosPayload.lib.mqtt import Topic
from EosPayload.lib.orcheostrator.device_container import DeviceContainer, StatusUpdate, Status


class HealthDriver(DriverBase):
    _health_command_queue = Queue()
    _drivers: dict[str, DeviceContainer] = {}

    def setup(self) -> None:
        super().setup()

        self.register_thread('device-command', self.device_read)

    def device_read(self, logger: logging.Logger) -> None:
        if self._mqtt:
            self._mqtt.user_data_set({'logger': logger, 'queue': self._health_command_queue})
            self._mqtt.register_subscriber(Topic.HEALTH_HEARTBEAT, self.health_latest_data)
        while True:
            if not HealthDriver._health_command_queue.empty():
                decoded_msg = HealthDriver._health_command_queue.get(block=False)
                logger.info(f"received health query command {decoded_msg}, sending response")
                self.health_reply()

            self.thread_sleep(logger, 5)

    def health_latest_data(self, client, user_data, message):
        try:
            try:
                packet = Packet.decode(message.payload)
                assert packet.data_header.data_type == Type.DRIVER_HEALTH_REPORT
            except Exception as e:
                user_data['logger'].error(f"failed to decode health packet: {e}")
                return

            user_data['logger'].info(f"received health packet from device id={packet.data_header.sender}")

            driver_health_report: DriverHealthReport = packet.body

            status_update = StatusUpdate(
                driver_id=packet.data_header.sender,
                status=Status.HEALTHY if driver_health_report.is_healthy else Status.UNHEALTHY,
                thread_count=driver_health_report.num_threads,
                reporter=packet.data_header.sender,
                effective=packet.data_header.generate_time
            )

            self._drivers[status_update.driver_id].update_status(
                status_update.status,
                status_update.thread_count,
                status_update.reporter,
                status_update.effective,
            )

            user_data['queue'].put(status_update)

        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing health_latest_data: {e}"
                                      f"\n{traceback.format_exc()}")

    def health_reply(self, client, user_data, message):
        try:
            packet = Packet.decode(message.payload)
            if packet.data_header.data_type != Type.HealthQuery:
                user_data['logger'].error(f"Incorrect type {packet.data_header.data_type}, expected HealthQuery")
                return

            decoded_packet = HealthQuery.decode(packet.body.encode())

            user_data['logger'].info(f"Received health_query command for device_id {decoded_packet.device_id}")

            response_header = DataHeader(
                data_type=Type.HealthResponse,
                sender=self.get_device_id(),
                priority=Priority.URGENT,
                destination=packet.data_header.sender
            )

            response = Packet(HealthResponse(decoded_packet.device_id, decoded_packet.response_type), response_header)
            client.send(Topic.RADIO_TRANSMIT, response)

        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing health_query: {e}"
                                      f"\n{traceback.format_exc()}")
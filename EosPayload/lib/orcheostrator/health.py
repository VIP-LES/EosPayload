from datetime import datetime, timedelta
from queue import Queue
import logging
import threading
import traceback

from EosLib import Device
from EosLib.packet.packet import Packet

from EosPayload.lib.mqtt.client import Client
from EosPayload.lib.orcheostrator.driver_container import DriverContainer, Status, StatusUpdate


class Health:

    @staticmethod
    def health_monitor(_client, user_data, message):
        try:
            packet = None
            try:
                packet = Packet.decode(message.payload)
            except Exception as e:
                user_data['logger'].error(f"failed to decode health packet: {e}")
                return

            user_data['logger'].info(f"received health packet from device id={packet.data_header.sender}")

            if packet.data_header.sender != user_data['device_id']:
                # extracts just the first two fields (is_healthy, thread_count), ignores the rest
                is_healthy, thread_count, _ = packet.body.decode('ascii').split(',', 2)

                status_update = StatusUpdate(
                    driver_id=packet.data_header.sender,
                    status=Status.HEALTHY if int(is_healthy) else Status.UNHEALTHY,
                    thread_count=thread_count,
                    reporter=packet.data_header.sender,
                    effective=packet.data_header.generate_time
                )

                user_data['queue'].put(status_update)
        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing health_monitor: {e}"
                                      f"\n{traceback.format_exc()}")

    @staticmethod
    def health_check(driver_list: dict[Device|str, DriverContainer], update_queue: Queue,
                     logger: logging.Logger) -> None:
        try:
            logger.info("Starting Health Check")
            while not update_queue.empty():
                status_update = update_queue.get()
                driver_list[status_update.driver_id].update_status(status_update)

            for key, driver in driver_list.items():
                # auto set terminated if it died
                if driver.status.status in [Status.HEALTHY, Status.UNHEALTHY]\
                        and (driver.process is None or not driver.process.is_alive()):
                    logger.critical(f"process for driver {key} is no longer running -- marking terminated")
                    driver.update_status(Status.TERMINATED)

                # auto set unhealthy if we haven't had a ping in the last 30s from this device
                if driver.status.status == Status.HEALTHY\
                        and driver.status.effective < (datetime.now() - timedelta(seconds=30)):
                    logger.critical(f"haven't received a health ping from driver {key} in 30s -- marking unhealthy")
                    driver.update_status(Status.UNHEALTHY)

            logger.info(Health.generate_report(driver_list))

            logger.info("Done Checking Health")
        except Exception as e:
            logger.critical("An exception occurred when attempting to perform health check:"
                            f" {e}\n{traceback.format_exc()}")

    @staticmethod
    def generate_report(driver_list: dict[Device|str, DriverContainer]) -> str:
        report = {}
        for status in Status:
            report[status] = []

        num_threads = threading.active_count()
        for key, driver in driver_list.items():
            the_key = key if driver.status in [Status.NONE, Status.INVALID] else driver.driver.get_device_pretty_id()
            report[driver.status].append(f"{the_key} ({driver.status.thread_count} threads)"
                                         f" as of {driver.status.effective} (reported by {driver.status.reporter}"
                                         f" [{Device(driver.status.reporter).name}])")
            num_threads += int(driver.status.thread_count)

        report_string = f"Health Report: \n{len(report[Status.HEALTHY])} drivers running"
        report_string += f"\n{num_threads} total threads in use ({threading.active_count()} by OrchEOStrator)"
        for status, reports in report.items():
            report_string += f"\n\t{status}:"
            for item in reports:
                report_string += f"\n\t\t{item}"

        return report_string

    @staticmethod
    def publish_health_update(mqtt: Client, logger: logging.Logger, device_id: Device, ):


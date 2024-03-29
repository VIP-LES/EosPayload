from datetime import datetime, timedelta
from multiprocessing import Process
from queue import Queue
import logging
import os
import threading
import time
import traceback

from EosLib.device import Device
from EosLib.format import Type
from EosLib.format.formats.health.driver_health_report import DriverHealthReport
from EosLib.packet.packet import Packet

from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST
from EosPayload.lib.mqtt.client import Client, Topic
from EosPayload.lib.orcheostrator.device_container import DeviceContainer, Status, StatusUpdate
from EosPayload.lib.config import OrcheostratorConfigParser


class OrchEOStrator:

    _drivers: dict[str, DeviceContainer]

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str, config_filepath: str):
        """ Constructor.  Initializes output location, logger, mqtt, and health monitoring. """
        self._logger: logging.Logger | None = None
        self._drivers = {}
        self.output_directory = output_directory
        if not os.path.exists(self.output_directory):
            raise ValueError(f"output location '{output_directory}' does not exist")
        self._output_mkdir('artifacts')
        self._output_mkdir('data')
        self._output_mkdir('logs')

        init_logging(os.path.join(self.output_directory, 'logs', 'orchEOStrator.log'))
        self._logger = logging.getLogger('orchEOStrator')
        self._logger.info("initialization complete")
        self._logger.info("beginning boot process in " + os.getcwd())

        config_parser = OrcheostratorConfigParser(self._logger, config_filepath)
        self.orcheostrator_config = config_parser.parse_config()

        self._health_queue = Queue()

        try:
            self._mqtt = Client(MQTT_HOST)
            self._mqtt.user_data_set({'logger': self._logger, 'queue': self._health_queue})
            self._mqtt.register_subscriber(Topic.HEALTH_HEARTBEAT, self.health_monitor)
        except Exception as e:
            self._logger.critical(f"Failed to setup MQTT: {e}\n{traceback.format_exc()}")

    def __del__(self):
        """ Destructor.  Terminates all drivers. """
        if self._logger:
            self._logger.info("shutting down")
        self.terminate()
        if self._logger:
            self._health_check()
        logging.shutdown()

    #
    # PUBLIC METHODS
    #

    def run(self) -> None:
        self._spawn_drivers()
        while True:
            self._health_check()
            time.sleep(10)
            # future: anything else OrchEOStrator is responsible for doing.  Perhaps handling "force terminate" commands
            #         or MQTT things

    def terminate(self) -> None:
        if self._logger:
            self._logger.info("terminating processes")
        for device_id, device_container in self._drivers.items():
            if device_container.status in [Status.INITIALIZED, Status.HEALTHY, Status.UNHEALTHY]:
                if self._logger:
                    self._logger.info(f"terminating process for device id {device_id}")
                device_container.process.terminate()
                device_container.process.close()
                device_container.update_status(Status.TERMINATED)

    #
    # PROTECTED HELPER METHODS
    #

    def _spawn_drivers(self) -> None:
        """ Enumerates over all the classes in the drivers dir and spins them up """
        self._logger.info("Spawning Drivers")
        driver_list = self.orcheostrator_config.enabled_devices

        for container in driver_list:
            driver = container.driver
            driver_config = container.config
            try:
                self._logger.info(f"spawning process for device '{driver_config.get('pretty_id')}' from"
                                  f" class '{driver.__name__}'")
                proc = Process(target=self._driver_runner, args=(driver, self.output_directory, driver_config), daemon=True)
                container.process = proc
                proc.start()
                time.sleep(0.5)
                if not proc.is_alive():
                    proc.close()
                    raise Exception("process is not alive after start")
                self._drivers[driver_config.get("device_id")] = container
            except Exception as e:
                self._logger.critical("A fatal exception occurred when attempting to load driver from"
                                      f" class '{driver.__name__}': {e}\n{traceback.format_exc()}")
                container.update_status(Status.INVALID)
                self._drivers['<' + driver.__name__ + '>'] = container
        self._logger.info("Done Spawning Drivers")

    @staticmethod
    def _driver_runner(cls, output_directory: str, config: dict) -> None:
        """ Wrapper to execute driver run() method.

        :param cls: the driver class.  Must have a run() method
        :param output_directory: the location to store output (logs, data, etc.)
        """
        cls(output_directory, config).run()

    @staticmethod
    def health_monitor(_client, user_data, message):
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

            user_data['queue'].put(status_update)
        except Exception as e:
            # this is needed b/c apparently an exception in a callback kills the mqtt thread
            user_data['logger'].error(f"an unhandled exception occurred while processing health_monitor: {e}"
                                      f"\n{traceback.format_exc()}")

    def _health_check(self) -> None:
        try:
            self._logger.info("Starting Health Check")
            while not self._health_queue.empty():
                status_update = self._health_queue.get()
                self._drivers[status_update.driver_id].update_status(
                    status_update.status,
                    status_update.thread_count,
                    status_update.reporter,
                    status_update.effective,
                )

            num_threads = threading.active_count()
            report = {}
            for status in Status:
                report[status] = []
            for key, driver in self._drivers.items():
                # auto set terminated if it died
                if driver.status in [Status.HEALTHY, Status.UNHEALTHY, Status.INITIALIZED] and (driver.process is None or not driver.process.is_alive()):
                    self._logger.critical(f"process for driver {key} is no longer running -- marking terminated")
                    if driver.process is not None:
                        driver.process.close()
                    driver.update_status(Status.TERMINATED)

                # auto set unhealthy if we haven't had a ping in the last 30s from this device
                if driver.status in [Status.INITIALIZED, Status.HEALTHY] \
                        and driver.status_since < (datetime.now() - timedelta(seconds=30)):
                    self._logger.critical(f"haven't received a health ping from driver {key} in 30s -- marking unhealthy")
                    driver.update_status(Status.UNHEALTHY)

                the_key = key if driver.status in [Status.NONE, Status.INVALID] else driver.config.get("pretty_id")
                report[driver.status].append(f"{the_key} ({driver.thread_count} threads)"
                                             f" as of {driver.status_since} (reported by {driver.status_reporter}"
                                             f" [{Device(driver.status_reporter).name}])")
                num_threads += int(driver.thread_count)

            report_string = f"Health Report: \n{len(report[Status.HEALTHY])} drivers running"
            report_string += f"\n{num_threads} total threads in use ({threading.active_count()} by OrchEOStrator)"
            for status, reports in report.items():
                report_string += f"\n\t{status}:"
                for item in reports:
                    report_string += f"\n\t\t{item}"
            self._logger.info(report_string)

            self._logger.info("Done Checking Health")
        except Exception as e:
            self._logger.critical("An exception occurred when attempting to perform health check:"
                                  f" {e}\n{traceback.format_exc()}")

    def _output_mkdir(self, subdirectory: str) -> None:
        """ Make a subdirectory of the output location (if it doesn't already exist)

        :param subdirectory: the name of the subdirectory
        """
        if not os.path.exists(os.path.join(self.output_directory, subdirectory)):
            os.mkdir(os.path.join(self.output_directory, subdirectory))

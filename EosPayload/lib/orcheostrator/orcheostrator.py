from datetime import datetime, timedelta
from multiprocessing import Process
from queue import Queue
import inspect
import json
import logging
import os
import re
import threading
import time
import traceback

import EosLib
from EosLib import Device
from EosLib.packet.packet import Packet

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST
from EosPayload.lib.mqtt.client import Client, Topic
from EosPayload.lib.orcheostrator.driver_container import DriverContainer, Status, StatusUpdate
import EosPayload.drivers as drivers


def get_pretty_id(config: dict) -> str:
    """ :return: a unique string identifier formed by concatenating the device_name
                 with the device_id (padded to 3 digits)
    """
    device_id =config.get("device_id")
    name = config.get("name")
    return f"{name}-{device_id:03}"

class OrchEOStrator:

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str, config: dict):
        """ Constructor.  Initializes output location, logger, mqtt, and health monitoring. """
        self._logger = None
        self._drivers = {}
        self.output_directory = output_directory
        if not os.path.exists(self.output_directory):
            raise ValueError(f"output location '{output_directory}' does not exist")
        self._output_mkdir('artifacts')
        self._output_mkdir('data')
        self._output_mkdir('logs')

        self.config = config

        init_logging(os.path.join(self.output_directory, 'logs', 'orchEOStrator.log'))
        self._logger = logging.getLogger('orchEOStrator')
        self._logger.info("initialization complete")
        self._logger.info("beginning boot process in " + os.getcwd())

        self._health_queue = Queue()

        try:
            self._mqtt = Client(MQTT_HOST)
            self._mqtt.user_data_set({'logger': self._logger, 'queue': self._health_queue})
            self._mqtt.register_subscriber(Topic.HEALTH_HEARTBEAT, self.health_monitor)
        except Exception as e:
            self._logger.critical(f"Failed to setup MQTT: {e}\n{traceback.format_exc()}")

    def __del__(self):
        """ Destructor.  Terminates all drivers. """
        self._logger.info("shutting down")
        self.terminate()
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
        self._logger.info("terminating processes")
        for device_id, driver in self._drivers.items():
            if driver.status in [Status.HEALTHY, Status.UNHEALTHY]:
                self._logger.info(f"terminating process for device id {device_id}")
                driver.process.terminate()
                driver.update_status(Status.TERMINATED)

    @staticmethod
    def valid_driver(driver) -> bool:
        """ Determines if given class is a valid driver.

        :param driver: the class in question
        :return: True if valid, otherwise False
        """
        base_drivers = ["DriverBase", "PositionAwareDriverBase"]
        return (
            (driver is not None)
            and inspect.isclass(driver)
            and issubclass(driver, DriverBase)
            and driver.__name__ not in base_drivers
        )

    @staticmethod
    def parse_config(config_path: str) -> dict:
        """ Parses a config file at the provided path

        :param config_path: the path to the config file
        :return: a validated config dict
        """
        valid_driver_classes = {}
        for attribute_name in dir(drivers):
            driver = getattr(drivers, attribute_name)
            if OrchEOStrator.valid_driver(driver):
                valid_driver_classes[attribute_name] = driver


        with open(config_path) as config_file:
            config = json.load(config_file)

        used_ids = []
        enabled_driver_list = []

        for driver_config in config['enabled_drivers']:
            # Automatically populate name if not provided
            if driver_config.get("name") is not None:
                driver_config['name'] = driver_config.get("name")
            else:
                # Convert default name from CamelCase to lowercase with dashes
                # Code snippet taken from https://github.com/jpvanhal/inflection
                driver_class_name = driver_config.get("driver_class")
                driver_class_name = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', driver_class_name)
                driver_class_name = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', driver_class_name)
                driver_class_name = driver_class_name.replace("_", "-")
                driver_class_name = driver_class_name.lower()

                driver_config['name'] = driver_class_name

            # Validate name
            driver_name = driver_config.get("name")
            if not driver_name.isascii() or not driver_name.replace("-", "").isalnum():
                raise ValueError("Driver names may only contain alphanumeric characters and hyphens.")

            # Validate ID
            driver_device_id = driver_config.get("device_id")
            if driver_device_id is None:
                raise ValueError("Driver ID Cannot be None.")
            if driver_device_id in used_ids:
                raise ValueError("Driver ID Must be unique.")
            try:
                driver_config["device_id"] = EosLib.Device[driver_config["device_id"]].value
            except KeyError:
                raise ValueError("Invalid Device ID.")

            used_ids.append(driver_device_id)

            new_driver_class = driver_config['driver_class']
            if new_driver_class in valid_driver_classes:
                for field in valid_driver_classes.get(new_driver_class).get_required_config_fields():
                    if driver_config.get("driver_settings") is None or driver_config.get("driver_settings").get(field) is None:
                        raise ValueError("Required driver setting not provided.")
                enabled_driver_list.append((valid_driver_classes[new_driver_class], driver_config))
            else:
                raise ValueError("Driver class does not exist.")

        config = {"enabled_drivers_list":enabled_driver_list}
        return config

    #
    # PROTECTED HELPER METHODS
    #

    def _spawn_drivers(self) -> None:
        """ Enumerates over all the classes in the drivers dir and spins them up """
        self._logger.info("Spawning Drivers")
        driver_list = self.config["enabled_drivers_list"]

        for driver_tuple in driver_list:
            driver = driver_tuple[0]
            driver_config = driver_tuple[1]
            container = DriverContainer(driver, config=driver_config)
            try:
                if driver_config.get("device_id") is None:
                    self._logger.error(f"can't spawn process for device from class '{driver.__name__}'"
                                       " because device id is not defined")
                    container.update_status(Status.INVALID)
                    self._drivers['<' + driver.__name__ + '>'] = container
                    continue
                self._logger.info(f"spawning process for device '{get_pretty_id(driver_config)}' from"
                                  f" class '{driver.__name__}'")
                proc = Process(target=self._driver_runner, args=(driver, self.output_directory, driver_config), daemon=True)
                container.process = proc
                container.update_status(Status.HEALTHY, 1)
                proc.start()
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
            except Exception as e:
                user_data['logger'].error(f"failed to decode health packet: {e}")
                return

            user_data['logger'].info(f"received health packet from device id={packet.data_header.sender}")

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
                if driver.status in [Status.HEALTHY, Status.UNHEALTHY] and (driver.process is None or not driver.process.is_alive()):
                    self._logger.critical(f"process for driver {key} is no longer running -- marking terminated")
                    driver.update_status(Status.TERMINATED)

                # auto set unhealthy if we haven't had a ping in the last 30s from this device
                if driver.status == Status.HEALTHY and driver.status_since < (datetime.now() - timedelta(seconds=30)):
                    self._logger.critical(f"haven't received a health ping from driver {key} in 30s -- marking unhealthy")
                    driver.update_status(Status.UNHEALTHY)

                the_key = key if driver.status in [Status.NONE, Status.INVALID] else get_pretty_id(driver.config)
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

    @staticmethod
    def _spin() -> None:
        """ Spins to keep the software alive.  Never returns. """
        while True:
            time.sleep(10)

    def _output_mkdir(self, subdirectory: str) -> None:
        """ Make a subdirectory of the output location (if it doesn't already exist)

        :param subdirectory: the name of the subdirectory
        """
        if not os.path.exists(os.path.join(self.output_directory, subdirectory)):
            os.mkdir(os.path.join(self.output_directory, subdirectory))

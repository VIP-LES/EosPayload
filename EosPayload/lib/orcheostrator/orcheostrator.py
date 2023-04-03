from multiprocessing import Process
from queue import Queue
import inspect
import logging
import os
import time
import traceback

from EosLib import Device

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST
from EosPayload.lib.mqtt.client import Client, Topic
from EosPayload.lib.orcheostrator.driver_container import DriverContainer, Status
from EosPayload.lib.orcheostrator.health import Health
import EosPayload.drivers as drivers


class OrchEOStrator:

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str):
        """ Constructor.  Initializes output location, logger, mqtt, and health monitoring. """
        self._logger = None
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

        self._health_queue = Queue()

        try:
            self._mqtt = Client(MQTT_HOST)
            self._mqtt.user_data_set({
                'device_id': Device.ORCHEOSTRATOR,
                'logger': self._logger,
                'queue': self._health_queue
            })
            self._mqtt.register_subscriber(Topic.HEALTH_HEARTBEAT, Health.health_monitor)
        except Exception as e:
            self._logger.critical(f"Failed to setup MQTT: {e}\n{traceback.format_exc()}")

    def __del__(self):
        """ Destructor.  Terminates all drivers. """
        self._logger.info("shutting down")
        self.terminate()
        Health.health_check(self._drivers, self._health_queue, self._logger)
        logging.shutdown()

    #
    # PUBLIC METHODS
    #

    def run(self) -> None:
        self._spawn_drivers()
        while True:
            Health.health_check(self._drivers, self._health_queue, self._logger)
            time.sleep(10)
            # future: anything else OrchEOStrator is responsible for doing.  Perhaps handling "force terminate" commands
            #         or MQTT things

    def terminate(self) -> None:
        self._logger.info("terminating processes")
        for device_id, driver in self._drivers.items():
            if driver.status in [Status.HEALTHY, Status.UNHEALTHY]:
                self._logger.info(f"terminating process for device id {device_id}")
                driver.process.terminate()
                driver.update_status(status=Status.TERMINATED)

    @staticmethod
    def valid_driver(driver) -> bool:
        """ Determines if given class is a valid driver.

        :param driver: the class in question
        :return: True if valid, otherwise False
        """
        return (
            (driver is not None)
            and inspect.isclass(driver)
            and issubclass(driver, DriverBase)
            and driver.__name__ != "DriverBase"
        )

    #
    # PROTECTED HELPER METHODS
    #

    def _spawn_drivers(self) -> None:
        """ Enumerates over all the classes in the drivers dir and spins them up """
        self._logger.info("Spawning Drivers")
        for attribute_name in dir(drivers):
            driver = getattr(drivers, attribute_name)
            if self.valid_driver(driver):
                container = DriverContainer(driver)
                try:
                    if driver.get_device_id() is None:
                        self._logger.error(f"can't spawn process for device from class '{driver.__name__}'"
                                           " because device id is not defined")
                        container.update_status(status=Status.INVALID)
                        self._drivers['<' + driver.__name__ + '>'] = container
                        continue
                    if not driver.enabled():
                        self._logger.warning(f"skipping device '{driver.get_device_pretty_id()}' from"
                                             f" class '{driver.__name__}' because it is not enabled")
                        container.update_status(status=Status.DISABLED)
                        self._drivers[driver.get_device_id()] = container
                        continue
                    self._logger.info(f"spawning process for device '{driver.get_device_pretty_id()}' from"
                                      f" class '{driver.__name__}'")
                    proc = Process(target=self._driver_runner, args=(driver, self.output_directory), daemon=True)
                    container.process = proc
                    container.update_status(status=Status.HEALTHY, thread_count=1)
                    proc.start()
                    self._drivers[driver.get_device_id()] = container
                except Exception as e:
                    self._logger.critical("A fatal exception occurred when attempting to load driver from"
                                          f" class '{driver.__name__}': {e}\n{traceback.format_exc()}")
                    container.update_status(status=Status.INVALID)
                    self._drivers['<' + driver.__name__ + '>'] = container
        self._logger.info("Done Spawning Drivers")

    @staticmethod
    def _driver_runner(cls, output_directory: str) -> None:
        """ Wrapper to execute driver run() method.

        :param cls: the driver class.  Must have a run() method
        :param output_directory: the location to store output (logs, data, etc.)
        """
        cls(output_directory).run()

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

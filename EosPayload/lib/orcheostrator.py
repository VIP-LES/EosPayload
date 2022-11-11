from multiprocessing import Process
import inspect
import logging
import os
import time
import traceback

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.logger import init_logging
import EosPayload.drivers as drivers


class OrchEOStrator:

    _logger = None
    _processes = {}

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str):
        """ Constructor.  Initializes output location and logger. """
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

    def __del__(self):
        """ Destructor.  Terminates all drivers. """
        self.terminate()
        logging.shutdown()

    #
    # PUBLIC METHODS
    #

    def run(self) -> None:
        self._spawn_drivers()
        # future: anything else OrchEOStrator is responsible for doing.  Perhaps handling "force terminate" commands
        #         or MQTT things
        self._spin()

    def terminate(self) -> None:
        self._logger.info("terminating processes")
        for device, proc in self._processes.items():
            self._logger.info(f"terminating process for device id {device}")
            proc.terminate()
        self._processes = {}

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
    # PRIVATE HELPER METHODS
    #

    def _spawn_drivers(self) -> None:
        self._logger.info("Spawning Drivers")
        for attribute_name in dir(drivers):
            driver = getattr(drivers, attribute_name)
            if self.valid_driver(driver):
                try:
                    if driver.get_device_id() is None:
                        self._logger.error(f"can't spawn process for device from class '{driver.__name__}'"
                                           " because device id is not defined")
                        continue
                    if not driver.enabled():
                        self._logger.warning(f"skipping device '{driver.get_device_pretty_id()}' from"
                                             f" class '{driver.__name__}' because it is not enabled")
                        continue
                    self._logger.info(f"spawning process for device '{driver.get_device_pretty_id()}' from"
                                      f" class '{driver.__name__}'")
                    proc = Process(target=self._driver_runner, args=(driver, self.output_directory), daemon=True)
                    self._processes[driver.get_device_id()] = proc
                    proc.start()
                except Exception as e:
                    self._logger.critical("A fatal exception occurred when attempting to load driver from"
                                          f" class '{driver.__name__}': {e}\n{traceback.format_exc()}")
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
            time.sleep(1)

    def _output_mkdir(self, subdirectory: str) -> None:
        """ Make a subdirectory of the output location (if it doesn't already exist)

        :param subdirectory: the name of the subdirectory
        """
        if not os.path.exists(os.path.join(self.output_directory, subdirectory)):
            os.mkdir(os.path.join(self.output_directory, subdirectory))

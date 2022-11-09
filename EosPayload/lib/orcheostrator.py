from multiprocessing import Process
import inspect
import logging
import os
import time

from EosPayload.lib.driver_base import DriverBase
import EosPayload.drivers as drivers


class OrchEOStrator:

    _logger = None
    _processes = {}

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self):
        """ Constructor.  Initializes logger. """
        log_fmt = '[%(asctime)s.%(msecs)03d] %(name)s.%(levelname)s: %(message)s'
        date_fmt = '%Y-%m-%dT%H:%M:%S'
        logging.basicConfig(filename='orchEOStrator.log',
                            filemode='a',
                            format=log_fmt,
                            datefmt=date_fmt,
                            level=logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(log_fmt, date_fmt))
        logging.getLogger('').addHandler(console)
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
                proc = Process(target=self._driver_runner, args=(driver,), daemon=True)
                self._processes[driver.get_device_id()] = proc
                proc.start()
        self._logger.info("Done Spawning Drivers")

    @staticmethod
    def _driver_runner(cls) -> None:
        """ Wrapper to execute driver run() method.

        :param cls: the driver class.  Must have a run() method
        """
        cls().run()

    @staticmethod
    def _spin() -> None:
        """ Spins to keep the software alive.  Never returns. """
        while True:
            time.sleep(1)

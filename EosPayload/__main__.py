import inspect
import logging
import os
import time
from multiprocessing import Process

from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.orcheostrator import runner
import EosPayload.drivers as drivers


if __name__ == '__main__':
    # initialize logger
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
    logger = logging.getLogger('orchEOStrator')
    logger.info("beginning boot process in " + os.getcwd())

    # dynamically spawn drivers from EosPayload.drivers
    processes = {}
    for attribute_name in dir(drivers):
        driver = getattr(drivers, attribute_name)
        if inspect.isclass(driver) and issubclass(driver, DriverBase) and driver.__name__ != "DriverBase"\
                and driver.enabled():
            if get_device_id() is None:
                logger.error(f"can't spawn process for device from class '{driver.__name__}'"
                             " because device id is not defined")
                continue
            logger.info(f"spawning process for device id '{get_device_id()}' from class '{driver.__name__}'")
            proc = Process(target=runner, args=(driver,))
            processes[get_device_id()] = proc
            proc.start()

    logger.info("sleeping")
    time.sleep(35)
    logger.info("terminating processes")
    for device, proc in processes.items():
        logger.info("terminating process for " + device)
        proc.terminate()

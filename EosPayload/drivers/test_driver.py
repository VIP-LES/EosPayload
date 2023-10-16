from random import randint
import logging

from EosPayload.lib.base_drivers.driver_base import DriverBase

# This example shows a very basic polled driver that logs data to CSV and transmits it to ground


class TestDriver(DriverBase):

    def setup(self) -> None:
        super().setup()
        self.register_thread("device-read", self.device_read)

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for data!")
        while True:
            # this is where you would poll a device for data or whatever
            data = randint(0, 256)
            print(f"received data: {data}, data^2: {data*data}")

            csv_row = [str(data), str(data*data)]

            # this saves data to a file
            try:
                self.data_log(csv_row)
            except Exception as e:
                logger.error(f"unable to log data: {e}")

            # this sends data to the radio to get relayed to the ground station
            try:
                # TODO: transmit using some format class i guess
                pass
            except Exception as e:
                logger.error(f"unable to transmit data: {e}")

            self.thread_sleep(logger, 3)

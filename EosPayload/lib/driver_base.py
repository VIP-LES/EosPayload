import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from threading import Thread

from EosPayload.lib import MQTT_HOST
from EosPayload.lib.mqtt import Topic
from EosPayload.lib.mqtt.client import Client


class DriverBase(ABC):

    __read_thread = None
    __command_thread = None
    __data_file = None
    __logger = None

    def __init__(self):
        self.__data_file = open(get_device_id() + '.dat', 'a')

        # set up logging
        log_fmt = '[%(asctime)s.%(msecs)03d] %(name)s.%(levelname)s: %(message)s'
        date_fmt = '%Y-%m-%dT%H:%M:%S'
        logging.basicConfig(filename=get_device_id() + '.log',
                            filemode='a',
                            format=log_fmt,
                            datefmt=date_fmt,
                            level=logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(log_fmt, date_fmt))
        logging.getLogger('').addHandler(console)
        self.logger = logging.getLogger(get_device_id())
        self.logger.info("logger initialized -- init complete")

    def __del__(self):
        self.__data_file.close()
        logging.shutdown()

    def run(self) -> None:
        self.logger.info("device starting up in " + os.getcwd())

        self.logger.info("running setup")
        self.setup()
        self.logger.info("setup complete")

        read_logger = logging.getLogger(get_device_id() + '.device_read')
        self.__read_thread = Thread(None, self.device_read, f"{get_device_id()}-read-thread",
                                    (), {"logger": read_logger})
        self.__read_thread.daemon = True
        self.__read_thread.start()
        command_logger = logging.getLogger(get_device_id() + '.device_command')
        self.__command_thread = Thread(None, self.device_command, f"{get_device_id()}-command-thread",
                                       (), {"logger": command_logger})
        self.__command_thread.daemon = True
        self.__command_thread.start()

        mqtt = None
        while self.is_healthy():
            if mqtt is None:
                try:
                    mqtt = Client(MQTT_HOST)
                    self.logger.info("mqtt connection established")
                except ConnectionError as e:
                    self.logger.warning(f"failed to establish mqtt connection: {e}")
            self.send_heartbeat(mqtt)
            time.sleep(10)
        self.logger.critical("device unhealthy: "
                             + "read_thread" if not self.__read_thread.is_alive() else "command thread"
                             + "terminated unexpectedly")

        self.logger.info("device terminating")

    def setup(self) -> None:
        pass

    def device_read(self, logger: logging.Logger) -> None:
        self.spin()

    def device_command(self, logger: logging.Logger) -> None:
        self.spin()

    @staticmethod
    def spin() -> None:
        while True:
            time.sleep(1)

    @staticmethod
    @abstractmethod
    def get_device_id() -> str:
        pass

    @staticmethod
    def enabled() -> bool:
        return True

    def is_healthy(self) -> bool:
        return self.__read_thread.is_alive() and self.__command_thread.is_alive()

    def send_heartbeat(self, mqtt: Client) -> bool:
        succeeded = False
        if mqtt:
            succeeded = mqtt.send(Topic.HEALTH_HEARTBEAT, get_device_id())
        if succeeded:
            self.logger.info("heartbeat sent")
        else:
            self.logger.warning("heartbeat failed to send")
        return succeeded

    def data_log(self, data: list[str]) -> None:
        timestamp = datetime.now().isoformat()
        data_str = ','.join([timestamp, *data]) + "\n"
        self.__data_file.write(data_str)
        self.__data_file.flush()

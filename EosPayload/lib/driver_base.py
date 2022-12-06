from abc import ABC, abstractmethod
from datetime import datetime
from threading import Thread
import logging
import os
import time

from paho.mqtt.client import MQTTMessageInfo

from EosLib.packet.data_header import DataHeader
from EosLib import Device, Priority, Type
from EosLib.packet.packet import Packet

from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST, Topic
from EosPayload.lib.mqtt.client import Client


class DriverBase(ABC):

    #
    # CLASS PROPERTIES
    #

    # private -- these variables should never be referenced by subclasses
    __read_thread = None
    __command_thread = None
    __data_file = None

    # protected -- these variables may be referenced by subclasses.  see restrictions below.
    _logger = None  # may be referenced by subclasses only in methods that run in the main thread (setup, cleanup, etc)
    _mqtt = None
    _output_directory = None

    #
    # CONFIGURATION
    #

    @staticmethod
    @abstractmethod
    def get_device_id() -> Device:
        """ [REQUIRED] Returns the unique Device ID defined in EosLib.
        IDs must be unique or there will be undefined behavior.
        Add device IDs by generating a new EosLib patch version and bumping the version number in requirements.txt
        Must be defined by subclass of DriverBase.

        :return: the device name
        """
        raise NotImplementedError("Drivers must implement a get_device_id method")

    @staticmethod
    @abstractmethod
    def get_device_name() -> str:
        """ [REQUIRED] Returns the string name or type of the device (eg, "temp-sensor").
        Only alphanumeric symbols and hyphens allowed.
        Must be defined by subclass of DriverBase.

        :return: the device name
        """
        raise NotImplementedError("Drivers must implement a get_device_name method")

    @classmethod
    def get_device_pretty_id(cls) -> str:
        """ :return: a unique string identifier formed by concatenating the device_name
                     with the device_id (padded to 3 digits)
        """
        return f"{cls.get_device_name()}-{cls.get_device_id():03}"

    @staticmethod
    def enabled() -> bool:
        """ [OPTIONAL] Defaults to True.

        :return: True if driver is enabled, False otherwise
        """
        return True

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str):
        """ Driver constructor.  Responsible for initialization tasks.
        Should never be overriden by subclasses.  Use the setup() method instead.
        Should only ever be invoked by orchEOStrator.
        """

        # Validate device name
        if not (self.get_device_name().isascii() and self.get_device_name().replace('-', '').isalnum()):
            raise GenericDriverException("Driver names may only contain alphanumeric characters and hyphens.")

        # set up output location and data file
        self._output_directory = output_directory
        # i don't think there's a need for validation here since orchEOStrator guarantees it's set up
        self.__data_file = open(os.path.join(self._output_directory, 'data', self.get_device_pretty_id() + '.dat'), 'a')

        # set up logging
        init_logging(os.path.join(self._output_directory, 'logs', self.get_device_pretty_id() + '.log'))
        self._logger = logging.getLogger(self.get_device_pretty_id())

        # set up mqtt
        self._mqtt = Client(MQTT_HOST)

        self._logger.info("init complete")

    def setup(self) -> None:
        """ [OPTIONAL] Subclass-defined method to initialize any variables.
        Executes in Driver Main Thread.
        Read-only data can be stored to self.<name> for use in child threads.
        Recommended to call super().setup() in first line of implementation.
        """
        pass

    def __del__(self):
        """ Driver destructor.  Responsible for cleanup tasks on graceful shutdown.
        Should never be overriden by subclasses.  Use the cleanup() method instead.
        """
        self.cleanup()
        self.__data_file.close()
        logging.shutdown()

    def cleanup(self):
        """ [OPTIONAL] Subclass-defined method to do any clean-up / deinitialization on graceful shutdown.
        Executes in Driver Main Thread.
        This method will not execute on an unexpected termination and therefore shouldn't be heavily relied upon.
        Recommended to call super().cleanup() in last line of implementation.
        """
        pass

    #
    # CORE METHODS
    #

    def run(self) -> None:
        """ The "main" function for the driver.  Invokes setup() and spawns threads.  Issues heartbeat messages.
        Executes in the Driver Main Thread.
        Should never be overriden by subclasses.  Use device_read or device_command instead.
        Should only ever be invoked by orchEOStrator.
        """

        if not self.enabled():
            self._logger.info("device is not enabled, terminating before startup")
            return

        self._logger.info("device starting up in " + os.getcwd())

        self._logger.info("running setup")
        self.setup()
        self._logger.info("setup complete")

        read_logger = logging.getLogger(self.get_device_pretty_id() + '.device_read')
        self.__read_thread = Thread(None, self.device_read, f"{self.get_device_id()}-read-thread",
                                    (), {"logger": read_logger})
        self.__read_thread.daemon = True
        self.__read_thread.start()
        command_logger = logging.getLogger(self.get_device_pretty_id() + '.device_command')
        self.__command_thread = Thread(None, self.device_command, f"{self.get_device_id()}-command-thread",
                                       (), {"logger": command_logger})
        self.__command_thread.daemon = True
        self.__command_thread.start()

        while True:
            if not self.is_healthy():
                self._logger.critical(
                    f"device unhealthy:"
                    f"\n\tread_thread running: {self.__read_thread.is_alive()}"
                    f"\n\tcommand thread running: {self.__command_thread.is_alive()}"
                )

            self.__send_heartbeat()
            time.sleep(10)

    def device_read(self, logger: logging.Logger) -> None:
        """ [OPTIONAL] Main function for Driver Read Thread.
        Used to read from device.
        Method should not return, which would terminate the thread.  Use self.spin() to keep alive.

        :param logger: can be used to log info / error messages to disk and console
        """
        logger.info("device_read not implemented for this driver")
        self.spin()

    def device_command(self, logger: logging.Logger) -> None:
        """ [OPTIONAL] Main function for Driver Command Thread.
        Used to write to device.
        Method should not return, which would terminate the thread.  Use self.spin() to keep alive.

        :param logger: can be used to log info / error messages to disk and console
        """
        logger.info("device_command not implemented for this driver")
        self.spin()

    #
    # UTILITY METHODS
    #

    @staticmethod
    def spin() -> None:
        """ Loops forever. """
        while True:
            time.sleep(1)

    def is_healthy(self) -> bool:
        """ Reports if the driver is operating properly

        :return: True if all threads are alive, False otherwise
        """

        return self.__read_thread.is_alive() and self.__command_thread.is_alive()

    def __send_heartbeat(self) -> bool:
        """ Dispatches a heartbeat message to MQTT.
        Should not be overriden or invoked by subclasses.

        :return: True if heartbeat successfully sent, False otherwise
        """
        succeeded = False
        if self._mqtt:
            status = ','.join([
                str(int(self.get_device_id())),
                datetime.now().isoformat(),
                str(int(self.is_healthy())),
                str(int(self.__read_thread.is_alive())),
                str(int(self.__command_thread.is_alive()))
            ])
            succeeded = self._mqtt.send(Topic.HEALTH_HEARTBEAT, status)
        if succeeded:
            self._logger.info("heartbeat sent")
        else:
            self._logger.warning("heartbeat failed to send")
        return succeeded

    def data_log(self, data: list[str]) -> bool:
        """ Logs row of data to a CSV file
        This function is not thread safe -- invoke from at most 1 thread.

        :param data: an array of strings
        :return: True on success, False otherwise
        """
        timestamp = datetime.now().isoformat()
        data_str = ','.join([timestamp, *data]) + "\n"
        self.__data_file.write(data_str)
        self.__data_file.flush()
        return True

    def data_transmit(self, data: list[str], telemetry: bool = False) -> MQTTMessageInfo:
        """ Sends row of simple CSV data to the ground station

        :param data: an array of strings
        :param telemetry: optional, defaults to False.  Set to True if this is telemetry data.
        """

        header = DataHeader(
            data_type=Type.TELEMETRY if telemetry else Type.DATA,
            sender=self.get_device_id(),
            priority=Priority.TELEMETRY if telemetry else Priority.DATA,
        )

        packet = Packet(
            body=bytes(','.join(data), encoding='utf8'),
            data_header=header,
        )

        return self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode())


class GenericDriverException(Exception):
    pass

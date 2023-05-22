import threading
from abc import ABC
from datetime import datetime
import logging
import os
import time
import traceback

from paho.mqtt.client import MQTTMessageInfo

from EosLib.packet.data_header import DataHeader
from EosLib import Priority, Type
from EosLib.device import Device

from EosLib.packet.packet import Packet

from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST, Topic
from EosPayload.lib.mqtt.client import Client

class DriverBase(ABC):

    #
    # CONFIGURATION
    #

    def get_device_id(self) -> Device:
        """ Returns the unique Device ID provided in provided the config file.
        IDs must be unique or there will be undefined behavior.

        :return: the device name
        """
        # Exists mostly for backwards compatibility
        return self._config.get('device_id')

    def get_device_name(self) -> str:
        """ Returns the string name or type of the device (eg, "temp-sensor") as set in provided the config file.
        Only alphanumeric symbols and hyphens allowed.

        :return: the device name
        """
        # Exists mostly for backwards compatibility
        return self._config.get('name')


    @staticmethod
    def read_thread_enabled() -> bool:
        """ [OPTIONAL] Defaults to False.  device_read() should be overriden if enabled

        :return: True if read thread is enabled, False otherwise.
        """
        return False

    @staticmethod
    def command_thread_enabled() -> bool:
        """ [OPTIONAL] Defaults to False.  device_command() should be overriden if enabled

        :return: True if command thread is enabled, False otherwise.
        """
        return False

    @staticmethod
    def get_required_config_fields() -> list[str]:
        """ [OPTIONAL] Defaults to empty list. Provides a list of names of required config fields which must be
        provided in the config json and which are guaranteed to be present in _device_config

        :return: List of required config fields.
        """
        return []

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str, config: dict):
        """ Driver constructor.  Responsible for initialization tasks.
        Should only be overriden by subclasses to initialize instance variables to zero-values/constants.
        Calling `super().__init__(output_directory)` at the beginning is required.
        For all other initialization purposes, use the setup() method instead.
        Should only ever be invoked by orchEOStrator.
        :param config:
        """

        #
        # CLASS PROPERTIES
        #

        # private -- these variables should never be referenced by subclasses
        self.__read_thread = None
        self.__command_thread = None
        self.__data_file = None

        # protected -- these variables may be referenced by subclasses.  see restrictions below.
        self._logger = None  # may be referenced by subclasses only in methods that run in the main thread (setup, cleanup, etc)
        self._mqtt = None
        self._output_directory = None

        self._config = config
        self._settings = config.get("settings")
        self._pretty_id = config.get("pretty_id")

        #
        # INITIALIZATION
        #

        # set up output location and data file
        self._output_directory = output_directory
        # I don't think there's a need for validation here since orchEOStrator guarantees it's set up
        self.__data_file = open(os.path.join(self._output_directory, 'data', self._pretty_id + '.dat'), 'a')

        # set up logging
        init_logging(os.path.join(self._output_directory, 'logs', self._pretty_id + '.log'))
        self._logger = logging.getLogger(self._pretty_id)

        # set up mqtt
        try:
            self._mqtt = Client(MQTT_HOST)
        except Exception as e:
            self._logger.critical(f"Failed to setup MQTT: {e}\n{traceback.format_exc()}")

        self._logger.info("init complete")

    def setup(self) -> None:
        """ [OPTIONAL] Subclass-defined method to initialize any variables.
        Executes in Driver Main Thread.
        Read-only instance data can be stored to self.<name> for use in child threads.
        Declare instance variables by overriding __init__ to set them to zero-values.  Define them here.
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

        self._logger.info("device starting up in " + os.getcwd())
        try:
            self._logger.info("running setup")
            try:
                self.setup()
            except Exception as err:
                self._logger.error(f"Error occurred while running setup: {err}\n{traceback.format_exc()}")
            self._logger.info("setup complete")

            # thread setup

            if self.read_thread_enabled():
                self._logger.info("starting read thread")
                read_logger = logging.getLogger(self._pretty_id + '.device_read')
                self.__read_thread = threading.Thread(
                    None,
                    self.__device_read_wrapper,
                    f"{self.get_device_id()}-read-thread",
                    (),
                    {"logger": read_logger}
                )
                self.__read_thread.daemon = True
                self.__read_thread.start()
            else:
                self._logger.info("skipping starting read thread because it is not enabled")

            if self.command_thread_enabled():
                self._logger.info("starting command thread")
                command_logger = logging.getLogger(self._pretty_id + '.device_command')
                self.__command_thread = threading.Thread(
                    None,
                    self.__device_command_wrapper,
                    f"{self.get_device_id()}-command-thread",
                    (),
                    {"logger": command_logger}
                )
                self.__command_thread.daemon = True
                self.__command_thread.start()
            else:
                self._logger.info("skipping starting command thread because it is not enabled")

            self._logger.info("device startup complete")

            # health check loop
            while True:
                if not self.is_healthy():
                    read_thread_message = "disabled"
                    if self.read_thread_enabled():
                        read_thread_message = str(self.__read_thread.is_alive())
                    command_thread_message = "disabled"
                    if self.command_thread_enabled():
                        command_thread_message = self.__command_thread.is_alive()
                    self._logger.error(
                        f"device unhealthy:"
                        f"\n\tread_thread running: {read_thread_message}"
                        f"\n\tcommand thread running: {command_thread_message}"
                    )

                self.__send_heartbeat()
                time.sleep(10)
        except Exception as err:
            self._logger.error(f"Error occurred in driver run() method: {err}\n{traceback.format_exc()}")

    def device_read(self, logger: logging.Logger) -> None:
        """ [OPTIONAL] Main function for Driver Read Thread.
        Used to read from device.
        Method should not return, which would terminate the thread.  Use self.spin() to keep alive.

        :param logger: can be used to log info / error messages to disk and console
        """
        logger.info("device_read not implemented for this driver")
        self.spin()

    def __device_read_wrapper(self, logger: logging.Logger) -> None:
        """ Runs the device_read function with exception reporting.  Do not override.

        :param logger: can be used to log info / error messages to disk and console
        """
        try:
            self.device_read(logger)
        except Exception as err:
            self._logger.critical(f"Fatal error occurred in read thread: {err}\n{traceback.format_exc()}")

    def device_command(self, logger: logging.Logger) -> None:
        """ [OPTIONAL] Main function for Driver Command Thread.
        Used to write to device.
        Method should not return, which would terminate the thread.  Use self.spin() to keep alive.

        :param logger: can be used to log info / error messages to disk and console
        """
        logger.info("device_command not implemented for this driver")
        self.spin()

    def __device_command_wrapper(self, logger: logging.Logger) -> None:
        """ Runs the device_command function with exception reporting.  Do not override.

        :param logger: can be used to log info / error messages to disk and console
        """
        try:
            self.device_command(logger)
        except Exception as err:
            self._logger.critical(f"Fatal error occurred in command thread: {err}\n{traceback.format_exc()}")

    #
    # UTILITY METHODS
    #

    @staticmethod
    def spin() -> None:
        """ Loops forever. """
        while True:
            time.sleep(10)

    def is_healthy(self) -> bool:
        """ Reports if the driver is operating properly

        :return: True if all threads are alive, False otherwise
        """

        read_thread_healthy = self.__read_thread.is_alive() if self.read_thread_enabled() else True
        command_thread_healthy = self.__command_thread.is_alive() if self.command_thread_enabled() else True

        return read_thread_healthy and command_thread_healthy

    def __send_heartbeat(self) -> bool:
        """ Dispatches a heartbeat message to MQTT.
        Should not be overriden or invoked by subclasses.

        Heartbeat syntax:
          single utf8-encoded CSV row of the following fields:
            is_healthy: 0 if unhealthy, 1 if healthy
            thread_count: number of threads in use
            read_thread_status: -1 if dead, 0 if disabled, 1 if running
            command_thread_status: -1 if dead, 0 if disabled, 1 if running

        :return: True if heartbeat successfully sent, False otherwise
        """
        succeeded = False
        if self._mqtt:
            header = DataHeader(
                data_type=Type.TELEMETRY,
                sender=self.get_device_id(),
                priority=Priority.NO_TRANSMIT,
            )
            read_thread_status = 0
            if self.read_thread_enabled():
                if self.__read_thread.is_alive():
                    read_thread_status = 1
                else:
                    read_thread_status = -1
            command_thread_status = 0
            if self.command_thread_enabled():
                if self.__command_thread.is_alive():
                    command_thread_status = 1
                else:
                    command_thread_status = -1
            status = ','.join([
                str(int(self.is_healthy())),
                str(threading.active_count()),
                str(read_thread_status),
                str(command_thread_status)
            ])
            packet = Packet(
                data_header=header,
                body=status.encode('utf8')
            )
            succeeded = False
            try:
                succeeded = self._mqtt.send(Topic.HEALTH_HEARTBEAT, packet.encode())
            except Exception as e:
                self._logger.error(f"exception occurred while attempting to send heartbeat: {e}"
                                   f"\n{traceback.format_exc()}")
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
        :return MQTTMessageInfo object or None on total failure -- see Paho docs
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

        return self._mqtt.send(Topic.RADIO_TRANSMIT, packet.encode()) if self._mqtt else None


class GenericDriverException(Exception):
    pass
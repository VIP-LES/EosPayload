from datetime import datetime
import logging
import os
import sys
import threading
import time
import traceback

from paho.mqtt.client import MQTTMessageInfo

from EosLib.packet.data_header import DataHeader
from EosLib import Priority, Type
from EosLib.device import Device

from EosLib.packet.packet import Packet

from EosPayload.lib.thread_container import ThreadStatus, ThreadContainer
from EosPayload.lib.logger import init_logging
from EosPayload.lib.mqtt import MQTT_HOST, Topic
from EosPayload.lib.mqtt.client import Client
from EosPayload.lib.util import validate_process_name


class DriverBase:

    _mqtt: Client | None
    __threads: dict[str, ThreadContainer]

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
    def get_required_config_fields() -> list[str]:
        """ [OPTIONAL] Defaults to empty list. Provides a list of names of required config fields which must be
        provided in the config json and which are guaranteed to be present in _device_config

        :return: List of required config fields.
        """
        return []

    #
    # INITIALIZATION AND DESTRUCTION METHODS
    #

    def __init__(self, output_directory: str, config: dict) -> None:
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
        self.__threads = {}
        self.__stop_signal = threading.Event()
        self.__data_file = None

        # protected -- these variables may be referenced by subclasses.  see restrictions below.
        self._logger = None  # may be referenced only in methods that run in the main thread (setup, cleanup, etc)
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

        # set up logging
        init_logging(os.path.join(self._output_directory, 'logs', self._pretty_id + '.log'))
        self._logger = logging.getLogger(self._pretty_id)

        self._logger.info("init complete")

    def setup(self) -> None:
        """ [OPTIONAL] Subclass-defined method to initialize any variables.
        Executes in Driver Main Thread.
        Read-only instance data can be stored to self.<name> for use in child threads.
        Declare instance variables by overriding __init__ to set them to zero-values.  Define them here.
        Recommended to call super().setup() in first line of implementation.
        """
        # unset stop signal if cleanup() was called prior
        if self.__stop_signal.is_set():
            self.__stop_signal.clear()

        # for completeness
        self.__threads['main'] = ThreadContainer('main', threading.main_thread(), ThreadStatus.ALIVE)

        # set up mqtt
        try:
            self._mqtt = Client(MQTT_HOST)
            self.__threads['mqtt'] = ThreadContainer('mqtt', self._mqtt.get_thread(), ThreadStatus.ALIVE)
        except Exception as e:
            self._logger.critical(f"Failed to setup MQTT: {e}\n{traceback.format_exc()}")

        # open data file
        self.__data_file = open(os.path.join(self._output_directory, 'data', self._pretty_id + '.dat'), 'a')

    def __del__(self):
        """ Driver destructor.  Responsible for cleanup tasks on graceful shutdown.
        Should never be overriden by subclasses.  Use the cleanup() method instead.
        """
        self.cleanup()
        logging.shutdown()

    def cleanup(self):
        """ [OPTIONAL] Subclass-defined method to do any clean-up / deinitialization on graceful shutdown.
        Executes in Driver Main Thread.
        This method will not execute on an unexpected termination and therefore shouldn't be heavily relied upon.
        Required to call super().cleanup() in last line of implementation.
        This method requests all non-main threads to terminate.  If stop_signal is not respected in a
        thread main function, or the thread is hanging, the cleanup will not in fact be clean
        """
        self._logger.info("Starting cleanup")

        # close data file
        self.__data_file.flush()
        self.__data_file.close()

        # kill mqtt client
        self._mqtt.loop_stop()  # blocking.  this will join the thread, no way around it sadly
        self._mqtt.disconnect()
        self._mqtt.__del__()  # explicitly closing sockets just in case
        self._mqtt = None

        # request shutdown for all registered threads
        self.__stop_signal.set()
        self.__threads = {}

        self._logger.info("Cleanup complete")

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

            self._logger.info("starting threads")
            thread_container: ThreadContainer
            for name, thread_container in self.__threads.items():
                if thread_container.status == ThreadStatus.REGISTERED:
                    try:
                        thread_container.thread.start()
                        thread_container.status = ThreadStatus.ALIVE
                    except RuntimeError as err:
                        self._logger.critical(f"failed to start thread '{name}': {err}\n{traceback.format_exc()}")
                        thread_container.status = ThreadStatus.INVALID

            self._logger.info("done starting threads")

            self._logger.info("device startup complete")

            # health check loop
            while True:
                if not self.is_healthy():
                    log_message = f"device unhealthy:"
                    for name, thread_container in self.__threads.items():
                        if thread_container.status == ThreadStatus.ALIVE and not thread_container.thread.is_alive():
                            thread_container.status = ThreadStatus.DEAD
                        log_message += f"\n\tthread-{name} status: {thread_container.status.name}"
                    self._logger.critical(log_message)

                self.__send_heartbeat()
                time.sleep(10)
        except Exception as err:
            self._logger.error(f"Error occurred in driver run() method: {err}\n{traceback.format_exc()}")

    #
    # THREADING METHODS
    #

    def register_thread(self, name: str, thread_main: callable) -> None:
        """ [OPTIONAL] Invoke this method in setup() to declare a driver thread.  Threads run in parallel
        (simultaneously) and you should take care to use thread-safe data structures and constructs for any shared
        data.

        :param name: a unique alphanumeric (+hyphens) identifier for the thread
        :param thread_main: the main function for the thread.  Should take three params: self, and a logging.Logger
                            object.  The function must use the provided logger not self._logger.  The function must
                            call self.check_stop_signal() at least once per second, which may also be accomplished by
                            calling self.thread_sleep() instead of time.sleep() within an infinite loop.  The function
                            should have return type None; any returned value will be ignored.
        """
        if not validate_process_name(name):
            self._logger.critical(f"Failed to register thread '{name}':"
                                  f" name must be alphanumeric (hyphens also allowed)")
            self.__threads[name] = ThreadContainer(name, None, ThreadStatus.INVALID)
            return
        elif name in self.__threads.keys():
            self._logger.critical(f"Failed to register thread '{name}':"
                                  f" a thread with the same name has already been registered")
            self.__threads[name] = ThreadContainer(name, None, ThreadStatus.INVALID)
            return

        full_name = f"{self.get_device_id()}-thread-{name}"
        thread_logger = logging.getLogger(self._pretty_id + f".thread-{name}")

        thread = threading.Thread(
            None,
            self.__thread_wrapper,
            full_name,
            (),
            {"logger": thread_logger, "thread_main": thread_main}
        )
        thread.daemon = True

        self.__threads[name] = ThreadContainer(name, thread, ThreadStatus.REGISTERED)
        self._logger.info(f"registered thread '{name}' with main method '{thread_main.__name__}'")

    @staticmethod
    def __thread_wrapper(logger: logging.Logger, thread_main: callable) -> None:
        """ Runs the thread_main function with exception reporting.  Do not override.

        :param logger: can be used to log info / error messages to disk and console
        :param thread_main: the main method for the thread
        """
        try:
            thread_main(logger)
        except Exception as err:
            logger.critical(f"Terminating due to fatal uncaught exception: {err}\n{traceback.format_exc()}")

    def check_stop_signal(self, logger: logging.Logger) -> None:
        """ Terminates the thread upon receiving the stop signal.
        This method must be periodically invoked by registered threads within the thread's main function.

        :param logger:
        """
        if self.__stop_signal.is_set():
            logger.info("Received stop signal, terminating")
            sys.exit()

    def thread_sleep(self, logger: logging.Logger, seconds: float) -> None:
        """ Sleeps a thread while secretly checking for the stop signal every second

        :param logger:
        :param seconds:
        """
        elapsed = 0.0
        while elapsed < seconds:
            sleep_seconds = min(seconds - elapsed, 1.0)
            time.sleep(sleep_seconds)
            elapsed += sleep_seconds
            self.check_stop_signal(logger)

    def thread_spin(self, logger: logging.Logger) -> None:
        """ Keeps a thread alive by spinning forever (unless the stop signal is received)

        :param logger:
        """
        while True:
            self.thread_sleep(logger, 1)

    #
    # HEALTH REPORTING METHODS
    #

    def is_healthy(self) -> bool:
        """ [OPTIONAL] Reports if the driver is operating properly

        :return: True if all threads are alive, False otherwise
        """

        all_threads_alive = True
        for thread_container in self.__threads.values():
            if thread_container.status != ThreadStatus.ALIVE:
                return False
            else:
                all_threads_alive &= thread_container.thread.is_alive()
        return all_threads_alive

    def __send_heartbeat(self) -> bool:
        """ Dispatches a heartbeat message to MQTT.
        Should not be overriden or invoked by subclasses.

        Heartbeat syntax:
          single utf8-encoded CSV row of the following fields:
            is_healthy: 0 if unhealthy, 1 if healthy
            thread_count: number of threads in use

        :return: True if heartbeat successfully sent, False otherwise
        """
        succeeded = False
        if self._mqtt:
            header = DataHeader(
                data_type=Type.TELEMETRY,
                sender=self.get_device_id(),
                priority=Priority.NO_TRANSMIT,
            )
            status = ','.join([
                str(int(self.is_healthy())),
                str(threading.active_count()),
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

    #
    # DATA REPORTING METHODS
    #

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

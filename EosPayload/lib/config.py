import inspect
import json
import logging
import os
import re

from EosLib import device

from EosPayload import drivers
from EosPayload.lib.driver_base import DriverBase
from EosPayload.lib.orcheostrator.device_container import DeviceContainer, Status

base_drivers = ["DriverBase", "PositionAwareDriverBase"]


class OrcheostratorConfig:
    def __init__(self):
        self.global_config = {}
        self.enabled_devices = []

class OrcheostratorConfigParser:

    config_indent = "\t"

    def __init__(self, logger: logging.Logger, config_filepath: str):
        self.logger = logger
        self.config_filepath = config_filepath
        self.orcheostrator_config = OrcheostratorConfig()
        self.used_device_ids = []
        self.available_drivers = {}
        self.disabled_drivers = []
        self.unused_drivers = {}

    def get_raw_config(self) -> dict | None:
        try:
            with open(self.config_filepath) as config_file:
                raw_config = json.load(config_file)
        except OSError:
            self.logger.critical("Unable to open config file")
            return None
        self.logger.info(f"Opened config file at {os.path.abspath(self.config_filepath)}")
        return raw_config

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
                and driver.__name__ not in base_drivers
        )

    @staticmethod
    def collect_available_drivers() -> dict[str, DriverBase]:
        available_drivers = {}
        for attribute_name in dir(drivers):
            driver = getattr(drivers, attribute_name)
            if OrcheostratorConfigParser.valid_driver(driver):
                available_drivers.update({attribute_name: driver})
        return available_drivers

    @staticmethod
    def get_pretty_id_from_config(config: dict) -> str:
        """ :return: a unique string identifier formed by concatenating the device_name
                     with the device_id (padded to 3 digits)
        """
        device_id = config.get("device_id")
        name = config.get("name")
        return f"{name}-{device_id:03}"

    def configure_device(self, device_config: dict) -> None:
        device_name = device_config.get("name")

        if device_name is not None and \
            (not device_name.isascii() or not device_name.replace("-", "").isalnum()):
            self.logger.error(f"Device name \"{device_name}\" is invalid, falling back to generated name")

        if device_name is None:
            # Convert default name from CamelCase to lowercase with dashes
            # Code snippet taken from https://github.com/jpvanhal/inflection
            device_name = device_config.get("driver_class")
            device_name = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', device_name)
            device_name = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', device_name)
            device_name = device_name.replace("_", "-")
            device_name = device_name.lower()

            device_config.update({"name": device_name})
            self.logger.info(f"No name provided, generated name {device_name}")


        self.logger.info(f"Configuring device \"{device_name}\"")

        if device_config.get("enabled") != "true":
            self.logger.info(f"{self.config_indent}Driver disabled, skipping")
            self.disabled_drivers.append(device_name)
            return

        device_id = device_config.get("device_id")
        if device_id is None:
            self.logger.error(f"{self.config_indent}No device ID provided, skipping.")
            return
        if device_id in self.used_device_ids:
            self.logger.error(f"{self.config_indent}Device ID {device_id} already in use, skipping.")
            return
        try:
            device_id = device.Device[device_config["device_id"]].value
            device_config.update({"device_id": device_id})
        except KeyError:
            self.logger.error(f"{self.config_indent}Device ID {device_id} is invalid, skipping.")

        self.logger.info(f"{self.config_indent}Device ID: {device_id}")
        self.used_device_ids.append(device_id)

        pretty_id = self.get_pretty_id_from_config(device_config)
        device_config.update({"pretty_id": pretty_id})
        self.logger.info(f"{self.config_indent}Pretty ID: {pretty_id}")

        driver_class_name = device_config.get("driver_class")
        self.logger.info(f"{self.config_indent}Driver Class: {driver_class_name}")

        if driver_class_name is None:
            self.logger.error(f"{self.config_indent}Driver Class is None, skipping")
            return

        if driver_class_name not in self.available_drivers:
            self.logger.error(f"{self.config_indent}Driver Class {driver_class_name} is not available, skipping")
            return

        driver_class = self.available_drivers.get(driver_class_name)
        driver_settings = device_config.get("driver_settings")
        if driver_settings:
            optional_driver_settings = device_config.get("driver_settings").copy()
        else:
            optional_driver_settings = device_config.get("driver_settings")

        if driver_class.get_required_config_fields():
            if driver_settings is None:
                self.logger.error(f"{self.config_indent}Driver settings are required but not provided, skipping")
                return
            self.logger.info(f"{self.config_indent}Required driver settings:")
            for required_config_field in driver_class.get_required_config_fields():
                if driver_settings.get(required_config_field) is None:
                    self.logger.error(f"{self.config_indent}{self.config_indent}Driver setting "
                                      f"{required_config_field} is required but not provided, skipping")
                    return
                else:
                    self.logger.info(f"{self.config_indent}{self.config_indent}{required_config_field}: "
                                     f"{driver_settings.get(required_config_field)}")
                    optional_driver_settings.pop(required_config_field)

        if optional_driver_settings:
            self.logger.info(f"{self.config_indent}Optional driver settings:")
            for driver_setting in optional_driver_settings:
                self.logger.info(f"{self.config_indent}{self.config_indent}{driver_setting}: "
                                 f"{optional_driver_settings.get(driver_setting)}")


        self.logger.info("Device config complete")
        device_container = DeviceContainer(driver_class, config=device_config)
        device_container.update_status(Status.INITIALIZED)
        self.orcheostrator_config.enabled_devices.append(device_container)
        if self.unused_drivers.get(driver_class_name):
            self.unused_drivers.pop(driver_class_name)

    def parse_config(self) -> OrcheostratorConfig:
        raw_config = self.get_raw_config()
        self.available_drivers = self.collect_available_drivers()
        self.unused_drivers = self.collect_available_drivers()
        device_configs = raw_config.pop("devices")
        self.orcheostrator_config.global_config = raw_config

        for device_config in device_configs:
            self.configure_device(device_config)

        unused_drivers_string = ", ".join(list(self.unused_drivers.keys()))
        self.logger.info(f"Existing drivers with no config: {unused_drivers_string}")

        disabled_drivers_string = ", ".join(self.disabled_drivers)
        self.logger.info(f"Configured but disabled drivers: {disabled_drivers_string}")

        return self.orcheostrator_config
# from random import randint
# import logging
# import time
# from smbus2 import SMBus
# from datetime import datetime
#
# from EosLib.packet.definitions import Device
# from EosPayload.lib.driver_base import DriverBase
#
#
# class RadioDriver(DriverBase):
#     @staticmethod
#     def get_device_id() -> Device:
#         return Device.RADIO
#
#     @staticmethod
#     def get_device_name() -> str:
#         return "RadioDriver"
#
#     def device_read(self, logger: logging.Logger) -> None:
#         return 0
#
#     def device_command(self, logger: logging.Logger) -> None:
#         return 0

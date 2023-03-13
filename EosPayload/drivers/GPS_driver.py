import logging
import time
import board
import busio
import adafruit_gps

from EosLib.packet.definitions import Device
from EosPayload.lib.driver_base import DriverBase

class GPSDriver(DriverBase):

    @staticmethod
    def enabled() -> bool:
        return True

    @staticmethod
    def get_device_id() -> Device:
        return Device.GPS

    @staticmethod
    def get_device_name() -> str:
        return "I2C-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
        uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
        gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial

        gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        gps.send_command(b"PMTK220,1000")

        while True:
            gps.update()
            time.sleep(1)

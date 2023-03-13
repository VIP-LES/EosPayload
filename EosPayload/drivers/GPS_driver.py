import logging
import time
import board
import busio
import adafruit_gps
import serial
import Adafruit_BBIO.UART as UART

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
        return "GPS-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    def device_read(self, logger: logging.Logger) -> None:
#
        UART.setup("UART1")
        GPS = serial.Serial('/dev/ttyS0', 9600)
        while (1):
            while GPS.inWaiting() == 0:
                pass
            NMEA = GPS.readline()
            logger.info(NMEA)

        '''
        logger.info("PIN ||||| 1")
        uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
        logger.info("PIN ||||| 2")
        gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
        logger.info("PIN ||||| 3")

        gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        gps.send_command(b"PMTK220,1000")
        logger.info("PIN ||||| 4")

        while True:
            gps.update()
            logger.info("PING X")
            time.sleep(1)

'''
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
        uart = serial.Serial('/dev/ttyO1', 9600)
        uart.close()
        uart.open()
        track_history = []

        logger.info("PIN ||||| 1")
        gps = adafruit_gps.GPS(uart, debug=False)
        logger.info("PIN ||||| 2")

        gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        gps.send_command(b"PMTK220,1000")

        timestamp = time.monotonic()
        while True:
            data = gps.read(32)  # read up to 32 bytes
            if data is not None:
                # convert bytearray to string
                data_string = "".join([chr(b) for b in data])
                logger.info(data_string)
                #print(data_string, end="")

            if time.monotonic() - timestamp > 5:
                # every 5 seconds...
                gps.send_command(b"PMTK605")  # request firmware version
                timestamp = time.monotonic()

def gps_converter(lat, lon, track_history):
    """ Rounds the lat/lon from GPS data and creates the list of coordinates that shows the previous route taken
    this removes the last 15 data points due to those not being as smoothed as earlier points"""
    try:
        lat = round(lat,5)
        lon = round(lon,5)

        noduplicates = track_history[-10:]
        if not [lon, lat] in noduplicates:
            track_history.append([lon, lat])

        outline = filter(track_history[-15:])
        track_history = track_history[:-15]

        for item in outline:
            item[0] = round(item[0],5)
            item[1] = round(item[1],5)
            track_history.append(item)
        lat = track_history[-5][1]
        lon = track_history[-5][0]
        return lat, lon, track_history
    except:
        return lat, lon, track_history

        #while (1):
        #    while GPS.inWaiting() == 0:
        #        pass
        #    NMEA = GPS.readline()
        #    logger.info(NMEA)

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
import logging
import time
import board
import busio
import adafruit_gps
import serial
import Adafruit_BBIO.UART as UART

from EosLib.device import Device
from EosPayload.lib.driver_base import DriverBase
from EosLib.format.position import Position

class GPSDriver(DriverBase):

    def setup(self) -> None:
        UART.setup("UART1")
        self.uart = serial.Serial(port="/dev/ttyO1", baudrate=9600)

        self.gps = adafruit_gps.GPS(self.uart, debug=False)

        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

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

        last_print = time.monotonic()
        while True:
            self.gps.update()
            current = time.monotonic()
            if current - last_print >= 1.0:
                last_print = current
                if not self.gps.has_fix:
                    # Try again if we don't have a fix yet.
                    logger.info("Waiting for fix...")
                    continue

                logger.info("=" * 40)
                logger.info(
                    "Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
                        self.gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
                        self.gps.timestamp_utc.tm_mday,  # struct_time object that holds
                        self.gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                        self.gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                        self.gps.timestamp_utc.tm_min,  # month!
                        self.gps.timestamp_utc.tm_sec,
                    )
                )

                logger.info("Latitude: {0:.6f} degrees".format(self.gps.latitude))
                logger.info("Longitude: {0:.6f} degrees".format(self.gps.longitude))
                if self.gps.altitude_m is not None:
                    logger.info("Altitude: {} meters".format(self.gps.altitude_m))

    def cleanup(self):
        self.uart.close()


'''
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

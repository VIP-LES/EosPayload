import logging
import queue
import adafruit_gps
import serial
import Adafruit_BBIO.UART as UART

from EosLib.device import Device
from EosLib.format.position import Position, FlightState
from EosLib.packet.packet import DataHeader, Packet
from EosLib.packet.definitions import Type, Priority
import datetime

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic


class GPSDriver(PositionAwareDriverBase):
    data_time_format = "%H:%M:%S %d/%m/%Y"

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.emit_rate = datetime.timedelta(seconds=1)
        self.transmit_rate = datetime.timedelta(seconds=10)
        self.state_update_rate = datetime.timedelta(seconds=15)
        self.position_timeout = datetime.timedelta(seconds=30)
        self.current_flight_state = FlightState.UNKNOWN
        self.old_position = None
        self.read_queue = queue.Queue(maxsize=10)
        self.gotten_first_fix = False
        self.last_transmit_time = datetime.datetime.now()
        self.uart = None
        self.gps = None

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-read', self.device_read)

        UART.setup("UART1")
        self.uart = serial.Serial(port="/dev/ttyO1", baudrate=9600)
        self.gps = adafruit_gps.GPS(self.uart, debug=False)

        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

    def device_read(self, logger: logging.Logger) -> None:

        while True:
            self.gps.update()
            if not self.gps.has_fix:
                # Try again if we don't have a fix yet.
                logger.info("Waiting for fix...")
                self.thread_sleep(logger, 1)
                continue

            logger.info("=" * 40)
            time_hr = self.gps.timestamp_utc.tm_hour
            time_min = self.gps.timestamp_utc.tm_min
            time_sec = self.gps.timestamp_utc.tm_sec
            time_day = self.gps.timestamp_utc.tm_mday
            time_month = self.gps.timestamp_utc.tm_mon
            time_year = self.gps.timestamp_utc.tm_year
            logger.info(
                "Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
                    time_month,  # Grab parts of the time from the
                    time_day,  # struct_time object that holds
                    time_year,  # the fix time.  Note you might
                    time_hr,  # not get all data like year, day,
                    time_min,  # month!
                    time_sec,
                )
            )

            gps_lat = self.gps.latitude
            gps_lon = self.gps.longitude
            gps_alt = self.gps.altitude_m
            gps_speed = self.gps.speed_knots
            gps_sat = self.gps.satellites

            logger.info("Latitude: {0:.6f} degrees".format(self.gps.latitude))
            logger.info("Longitude: {0:.6f} degrees".format(self.gps.longitude))
            if self.gps.altitude_m is not None:
                logger.info("Altitude: {} meters".format(self.gps.altitude_m))

            # time
            try:
                # "%H:%M:%S %d/%m/%Y"
                data_datetime_string = "{:02}:{:02}:{:02} {}/{}/{}".format(time_hr, time_min, time_sec, time_day,
                                                                           time_month, time_year)
                data_datetime = datetime.datetime.strptime(data_datetime_string, GPSDriver.data_time_format)
                date_time = str(data_datetime.timestamp())
            except Exception:
                date_time = str(datetime.datetime.now())

            logger.info(date_time)

            position_bytes = Position.encode_position(float(date_time), float(gps_lat),
                                                      float(gps_lon), float(gps_alt),
                                                      float(gps_speed), int(gps_sat),
                                                      self.current_flight_state)

            gps_packet = Packet(position_bytes, DataHeader(Device.GPS, Type.POSITION, Priority.TELEMETRY))

            if self.gotten_first_fix is False:
                position = Position.decode_position(gps_packet)
                if position.valid:
                    self.gotten_first_fix = True
                    logger.info("Got first GPS fix")

            self._mqtt.send(Topic.POSITION_UPDATE, gps_packet.encode())
            if datetime.datetime.now() - self.last_transmit_time > self.transmit_rate:
                self._mqtt.send(Topic.RADIO_TRANSMIT, gps_packet.encode())
                self.last_transmit_time = datetime.datetime.now()

            self.thread_sleep(logger, 1)

    def cleanup(self):
        self.uart.close()

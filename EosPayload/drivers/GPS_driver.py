import logging
import queue
import traceback

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

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
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

            time_hr = self.gps.timestamp_utc.tm_hour
            time_min = self.gps.timestamp_utc.tm_min
            time_sec = self.gps.timestamp_utc.tm_sec
            time_day = self.gps.timestamp_utc.tm_mday
            time_month = self.gps.timestamp_utc.tm_mon
            time_year = self.gps.timestamp_utc.tm_year

            gps_lat = self.gps.latitude
            gps_long = self.gps.longitude
            gps_alt = self.gps.altitude_m
            gps_speed = self.gps.speed_knots
            gps_sat = self.gps.satellites

            # time
            try:
                # "%H:%M:%S %d/%m/%Y"
                data_datetime_string = "{:02}:{:02}:{:02} {}/{}/{}".format(time_hr, time_min, time_sec, time_day,
                                                                           time_month, time_year)
                data_datetime = datetime.datetime.strptime(data_datetime_string, GPSDriver.data_time_format)
                date_time = data_datetime.timestamp()
            except Exception as e:
                data_datetime = datetime.datetime.now()
                date_time = data_datetime.timestamp()
                logger.warning(f"Error parsing timestamp from GPS: {e}\n{traceback.format_exc()}"
                               f"\nGPS time parts: hour={time_hr}, min={time_min}, sec={time_sec}, day={time_day}"
                               f", month={time_month}, year={time_year}"
                               "\nusing current system time instead")

            data_points = [date_time, gps_lat, gps_long, gps_alt, gps_speed, gps_sat]
            try:
                self.data_log([str(datum) for datum in data_points])
            except Exception as e:
                logger.warning(f"exception thrown while logging data: {e}\n{traceback.format_exc()}")

            if None in data_points:
                logger.warning(f"Invalid GPS packet: time={date_time}, lat={gps_lat}, long={gps_long}"
                               f", alt={gps_alt}, speed={gps_speed}, sat={gps_sat}")
            else:
                position_bytes = Position.encode_position(date_time, float(gps_lat),
                                                          float(gps_long), float(gps_alt),
                                                          float(gps_speed), int(gps_sat),
                                                          self.current_flight_state)

                gps_packet = Packet(position_bytes, DataHeader(Device.GPS, Type.POSITION, Priority.TELEMETRY))

                if self.gotten_first_fix is False:
                    position = Position.decode_position(gps_packet)
                    if position.valid:
                        self.gotten_first_fix = True
                        logger.info("Got first valid GPS fix")

                self._mqtt.send(Topic.POSITION_UPDATE, gps_packet.encode())
                if datetime.datetime.now() - self.last_transmit_time > self.transmit_rate:
                    self._mqtt.send(Topic.RADIO_TRANSMIT, gps_packet.encode())
                    self.last_transmit_time = datetime.datetime.now()

            self.thread_sleep(logger, 1)

    def cleanup(self):
        self.uart.close()
        super().cleanup()

import logging
import time
import queue
import adafruit_gps
import serial
import Adafruit_BBIO.UART as UART

from EosLib.device import Device
from EosLib.format.position import Position, FlightState
from EosLib.packet.packet import DataHeader, Packet
from EosLib.packet.definitions import Type, Priority
import datetime

from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic


class GPSDriver(PositionAwareDriverBase):
    data_time_format = "%H:%M:%S %d/%m/%Y"

    def __int__(self, output_directory: str):
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
        UART.setup("UART1")
        self.uart = serial.Serial(port="/dev/ttyO1", baudrate=9600)
        self.gps = adafruit_gps.GPS(self.uart, debug=False)

        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.GPS

    @staticmethod
    def get_device_name() -> str:
        return "GPS-Driver"

    @staticmethod
    def read_thread_enabled() -> bool:
        return True

    @staticmethod
    def command_thread_enabled() -> bool:
        return False # CHANGE

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

    def device_command(self, logger: logging.Logger) -> None:
        last_emit_time = datetime.datetime.now()
        last_state_update_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while True:
            #incoming_raw_data = self.read_queue.get()
            #incoming_processed_data, incoming_data_dict = self.process_raw_esp_data(incoming_raw_data)
            #incoming_processed_data.append(str(self.gotten_first_fix))
            #self.data_log(incoming_processed_data)
            if (datetime.datetime.now() - last_emit_time) > self.emit_rate:
                last_emit_time = datetime.datetime.now()
            #    self.emit_data(incoming_data_dict, logger)
            if (datetime.datetime.now() - last_state_update_time) > self.state_update_rate:
                if self.old_position is None or self.latest_position.local_time is None:
                    self.old_position = self.latest_position
                elif (datetime.datetime.now() - self.latest_position.local_time) > self.position_timeout:
                    self.current_flight_state = FlightState.UNKNOWN
                elif self.latest_position.altitude < 1000:
                    self.current_flight_state = FlightState.ON_GROUND
                elif self.latest_position.altitude >= self.old_position.altitude:
                    self.current_flight_state = FlightState.ASCENT
                elif self.latest_position.altitude < self.old_position.altitude:
                    self.current_flight_state = FlightState.DESCENT
                else:
                    self.current_flight_state = FlightState.UNKNOWN
                self.old_position = self.latest_position
                last_state_update_time = datetime.datetime.now()

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

import serial
import logging
import datetime
import traceback

from ublox_gps import UbloxGps

from EosPayload.lib.base_drivers.position_aware_driver_base import PositionAwareDriverBase
from EosLib.format.formats.position import Position, FlightState
from EosLib.packet.packet import Packet, DataHeader
from EosLib.device import Device
from EosLib.packet.definitions import Priority
from EosLib.format.definitions import Type

from EosPayload.lib.mqtt import Topic


class NewGPSDriver(PositionAwareDriverBase):
    data_time_format = "%H:%M:%S %d/%m/%Y"

    def __init__(self, output_directory: str, config: dict) -> None:
        super().__init__(output_directory, config)
        self.current_flight_state = FlightState.UNKNOWN
        self.gotten_first_fix = False
        self.last_transmit_time = datetime.datetime.now()
        self.uart = None
        self.gps = None

    def setup(self) -> None:
        super().setup()

        self.register_thread('device-read', self.device_read)
        self.uart = serial.Serial('/dev/ttyO1', baudrate=9600, timeout=1)
        self.gps = UbloxGps(self.uart)

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting GPS Driver!")
        while True:
            geo = self.gps.geo_coords()
            if geo.fixType == 0:
                # Try again if we don't have a fix yet.
                logger.info("Waiting for fix...")
                self.thread_sleep(logger, 1)
                continue

            gps_time = self.gps.date_time()
            time_sec = gps_time.sec
            time_min = gps_time.min
            time_hr = gps_time.hour
            time_day = gps_time.day
            time_month = gps_time.month
            time_year = gps_time.year

            # https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf
            # page 304
            gps_lat = geo.lat  # deg
            gps_long = geo.lon  # deg
            gps_alt = geo.hMSL  # mm
            gps_speed = geo.speed  # mm/s (3D speed)
            gps_sat = geo.numSvs  # num satellites

            # time
            try:
                # "%H:%M:%S %d/%m/%Y"
                data_datetime_string = "{:02}:{:02}:{:02} {}/{}/{}".format(time_hr, time_min, time_sec, time_day,
                                                                           time_month, time_year)
                data_datetime = datetime.datetime.strptime(data_datetime_string, NewGPSDriver.data_time_format)
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
                position = Position(data_datetime, float(gps_lat), float(gps_long), float(gps_alt),
                                    float(gps_speed), int(gps_sat), self.current_flight_state)

                gps_packet = Packet(position, DataHeader(Device.GPS, Type.POSITION, Priority.TELEMETRY))
                if self.gotten_first_fix is False:
                    if position.valid:
                        self.gotten_first_fix = True
                        logger.info("Got first valid GPS fix")

                self._mqtt.send(Topic.POSITION_UPDATE, gps_packet)
                self.last_transmit_time = datetime.datetime.now()

            self.thread_sleep(logger, 1)

    def cleanup(self):
        if self.uart:
            self.uart.close()
        super().cleanup()

import queue
import re
import logging
import serial
import datetime

from EosLib.packet.definitions import Device, Type, Priority
from EosLib.packet.packet import DataHeader, Packet
from EosLib.format.Position import Position, FlightState

from EosPayload.lib.position_aware_driver_base import PositionAwareDriverBase
from EosPayload.lib.mqtt import Topic


class EngineeringDataDriver(PositionAwareDriverBase):
    esp_data_format = ["HR:MM:SEC", "MONTH/DAY", "LAT", "LONG", "speed", "altitude", "#ofSatellites", "accInX",
                       "accInY", "accInZ", "gyroX", "gyroY", "gyroZ", "IMU-temp", "pressure", "BME-temp",
                       "humidity"]
    esp_data_time_format = "%H:%M:%S %m/%d/%Y"

    # TODO: Move everything out of init
    def __init__(self):
        super().__init__()
        self.esp_port = "/dev/ttyUSB0"
        self.esp_baud = 115200
        self.ser_connection = None
        self.emit_rate = datetime.timedelta(seconds=1)
        self.state_update_rate = datetime.timedelta(seconds=15)
        self.position_timeout = datetime.timedelta(seconds=30)
        self.current_flight_state = FlightState.UNKNOWN
        self.old_position = None
        self.read_queue = queue.Queue(maxsize=10)

    @staticmethod
    def enabled() -> bool:
        return False

    @staticmethod
    def get_device_id() -> Device:
        return Device.MISC_ENGINEERING_1

    @staticmethod
    def get_device_name() -> str:
        return "engineering-data-driver"

    @staticmethod
    def dm_to_sd(dm):
        """
        Converts a geographic co-ordinate given in "degrees/minutes" dddmm.mmmm
        format (eg, "12319.943281" = 123 degrees, 19.943281 minutes) to a signed
        decimal (python float) format
        """
        # '12319.943281'
        dm = str(dm)
        if not dm or dm == '0.0':
            return 0.
        d, m = re.match(r'^(\d+)(\d\d\.\d+)$', dm).groups()
        return float(d) + float(m) / 60

    @staticmethod
    def process_raw_esp_data(raw_data) -> ([str], dict):
        list_data = raw_data.replace('\x00', '').split(',')
        data_dict = dict(zip(EngineeringDataDriver.esp_data_format, list_data))

        # TODO: Find a better solution for the year before 2023 please
        data_datetime_string = data_dict["HR:MM:SEC"] + " " + data_dict["MONTH/DAY"] + "/2022"
        data_datetime = datetime.datetime.strptime(data_datetime_string, EngineeringDataDriver.esp_data_time_format)
        data_dict['datetime'] = str(data_datetime.timestamp())
        data_dict['LAT'] = data_dict['LAT'].replace('N', '').replace('S', '')
        data_dict['LAT'] = EngineeringDataDriver.dm_to_sd(float(data_dict['LAT']))
        data_dict['LONG'] = data_dict['LONG'].replace('E', '').replace('W', '')
        data_dict['LONG'] = EngineeringDataDriver.dm_to_sd(float(data_dict['LONG']))
        data_dict['LONG'] *= -1  # TODO: do this in a way that doesn't make me want to cry

        data_dict['altitude'] = float(data_dict['altitude']) * 3.281  # Convert to feet

        return list_data, data_dict

    def setup(self) -> None:
        self.ser_connection = serial.Serial(self.esp_port, self.esp_baud)

    def fetch_data(self) -> str:  # This function might seem weird, but it exists to make mocking easier
        return self.ser_connection.readline().decode()[:-1]

    def is_alive(self):
        return self.ser_connection.isOpen()

    def emit_data(self, data_dict, logger):
        position_bytes = Position.encode_position(float(data_dict['datetime']), float(data_dict['LAT']),
                                                  float(data_dict['LONG']), float(data_dict['altitude']),
                                                  float(data_dict['speed']), int(data_dict['#ofSatellites']),
                                                  self.current_flight_state)

        gps_packet = Packet(position_bytes, DataHeader(Device.GPS, Type.POSITION, Priority.TELEMETRY))

        self._mqtt.send(Topic.RADIO_TRANSMIT, gps_packet.encode())
        self._mqtt.send(Topic.POSITION_UPDATE, gps_packet.encode())
        logger.info(f"Emitting position, lat: {float(data_dict['LAT'])}, long: {float(data_dict['LONG'])}, altitude: "
                    f"{float(data_dict['altitude'])}")

    def device_read(self, logger: logging.Logger) -> None:
        while self.is_alive():
            try:
                self.read_queue.put(self.fetch_data(), block=False)
            except queue.Full:
                pass

    def device_command(self, logger: logging.Logger) -> None:
        last_emit_time = datetime.datetime.now()
        last_state_update_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while True:
            incoming_raw_data = self.read_queue.get()
            incoming_processed_data, incoming_data_dict = self.process_raw_esp_data(incoming_raw_data)
            self.data_log(incoming_processed_data)
            if (datetime.datetime.now() - last_emit_time) > self.emit_rate:
                last_emit_time = datetime.datetime.now()
                self.emit_data(incoming_data_dict, logger)
            if (datetime.datetime.now() - last_state_update_time) > self.state_update_rate:
                if self.old_position is None:
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

    def cleanup(self):
        self.ser_connection.close()

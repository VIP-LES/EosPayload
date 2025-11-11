
from datetime import datetime
import logging
import traceback

from EosLib.format import Type
from EosLib.format.formats.science_data import ScienceData
from EosLib.packet import Packet
from EosLib.packet.definitions import Priority
from EosLib.packet.data_header import DataHeader

from EosPayload.lib.base_drivers.driver_base import DriverBase
import asyncio
import pycyphal
from pycyphal.transport.can import CANTransport
from pycyphal.transport.can.media.socketcan import SocketCANMedia
from pycyphal.transport import (
    PayloadMetadata,
    MessageDataSpecifier,
    InputSessionSpecifier
)


class ScienceDriver(DriverBase):

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)

        # initialize media socket
        media = SocketCANMedia(
            iface_name="can0",  # Use vcan0 for virtual CAN testing
            mtu=64  # 64 bytes = CAN FD mode
        )
        self.transport = CANTransport(
            media,
            local_node_id=41  # FIXME get id from Matthew
        )


        self.count = 0
        self.i2c_bus: I2C | None = None
        self.temp_humidity_sensor: SHTC3 | None = None
        self.barometer: BMP3XX_I2C | None = None
        self.uv_light_sensor: LTR390 | None = None
        self.ir_light_sensor: TSL2591 | None = None
        self.air_quality_sensor: PM25_I2C | None = None

    def setup(self) -> None:
        super().setup()

        try:
            pin
        except NameError:
            raise Exception("failed to import pin library")

        self.register_thread('device-read', self.device_read)

        # I know this is ugly, should probably be fixed later
        session_spec_temp_1 = InputSessionSpecifier(MessageDataSpecifier(subject_id=1300), remote_node_id=None)
        session_spec_humidity = InputSessionSpecifier(MessageDataSpecifier(subject_id=1301), remote_node_id=None)
        session_spec_temp_2 = InputSessionSpecifier(MessageDataSpecifier(subject_id=1302), remote_node_id=None)
        session_spec_pressure = InputSessionSpecifier(MessageDataSpecifier(subject_id=1303), remote_node_id=None)
        session_spec_altitude = InputSessionSpecifier(MessageDataSpecifier(subject_id=1304), remote_node_id=None)
        session_spec_ambient_light_count = InputSessionSpecifier(MessageDataSpecifier(subject_id=1305), remote_node_id=None)
        session_spec_ambient_light_lux = InputSessionSpecifier(MessageDataSpecifier(subject_id=1306), remote_node_id=None)
        session_spec_uv_count = InputSessionSpecifier(MessageDataSpecifier(subject_id=1307), remote_node_id=None)
        session_spec_uv_index = InputSessionSpecifier(MessageDataSpecifier(subject_id=1308), remote_node_id=None)
        session_spec_infrared_count = InputSessionSpecifier(MessageDataSpecifier(subject_id=1309), remote_node_id=None)
        session_spec_visible_count = InputSessionSpecifier(MessageDataSpecifier(subject_id=1310), remote_node_id=None)
        session_spec_full_spectrum_count = InputSessionSpecifier(MessageDataSpecifier(subject_id=1311), remote_node_id=None)
        session_spec_ir_visible_lux = InputSessionSpecifier(MessageDataSpecifier(subject_id=1312), remote_node_id=None)
        session_spec_pm10_standard = InputSessionSpecifier(MessageDataSpecifier(subject_id=1313), remote_node_id=None)
        session_spec_pm25_standard = InputSessionSpecifier(MessageDataSpecifier(subject_id=1314), remote_node_id=None)
        session_spec_pm100_standard = InputSessionSpecifier(MessageDataSpecifier(subject_id=1315), remote_node_id=None)
        session_spec_pm10_environmental = InputSessionSpecifier(MessageDataSpecifier(subject_id=1316), remote_node_id=None)
        session_spec_pm25_environmental = InputSessionSpecifier(MessageDataSpecifier(subject_id=1317), remote_node_id=None)
        session_spec_pm100_environmental = InputSessionSpecifier(MessageDataSpecifier(subject_id=1318), remote_node_id=None)
        session_spec_particulate_03um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1319), remote_node_id=None)
        session_spec_particulate_05um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1320), remote_node_id=None)
        session_spec_particulate_10um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1321), remote_node_id=None)
        session_spec_particulate_25um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1322), remote_node_id=None)
        session_spec_particulate_50um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1323), remote_node_id=None)
        session_spec_particulate_100um = InputSessionSpecifier(MessageDataSpecifier(subject_id=1324), remote_node_id=None)

        sensor_sessions = {
            "temp_1": session_spec_temp_1,
            "humidity": session_spec_humidity,
            "temp_2": session_spec_temp_2,
            "pressure": session_spec_pressure,
            "altitude": session_spec_altitude,
            "ambient_light_count": session_spec_ambient_light_count,
            "ambient_light_lux": session_spec_ambient_light_lux,
            "uv_count": session_spec_uv_count,
            "uv_index": session_spec_uv_index,
            "infrared_count": session_spec_infrared_count,
            "visible_count": session_spec_visible_count,
            "full_spectrum_count": session_spec_full_spectrum_count,
            "ir_visible_lux": session_spec_ir_visible_lux,
            "pm10_standard": session_spec_pm10_standard,
            "pm25_standard": session_spec_pm25_standard,
            "pm100_standard": session_spec_pm100_standard,
            "pm10_environmental": session_spec_pm10_environmental,
            "pm25_environmental": session_spec_pm25_environmental,
            "pm100_environmental": session_spec_pm100_environmental,
            "particulate_03um": session_spec_particulate_03um,
            "particulate_05um": session_spec_particulate_05um,
            "particulate_10um": session_spec_particulate_10um,
            "particulate_25um": session_spec_particulate_25um,
            "particulate_50um": session_spec_particulate_50um,
            "particulate_100um": session_spec_particulate_100um,
        }

        self.subscribers = {
            name: self.transport.get_input_session(spec, PayloadMetadata(64))
            for name, spec in sensor_sessions.items()
        }

    def cleanup(self):
        if self.i2c_bus is not None:
            self.i2c_bus.deinit()
        super().cleanup()

    async def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting to poll for science data via CAN!")

        counter = 0

        # Create a local reference for performance
        subs = self.subscribers

        while True:
            counter += 1
            try:
                # Wait for all sensor messages concurrently (timeout = 1s)
                results = await asyncio.gather(
                    *[sub.receive(asyncio.get_event_loop().time() + 1.0) for sub in subs.values()],
                    return_exceptions=True
                )

                # Extract payloads (skip any failed or None responses)
                sensor_values = {}
                for (name, result) in zip(subs.keys(), results):
                    if isinstance(result, Exception):
                        logger.warning(f"Exception while receiving {name}: {result}")
                        continue
                    if result is not None and hasattr(result, "fragmented_payload"):
                        # Assuming each message’s payload is a list/array-like of numeric values
                        # If messages use another structure, adapt here
                        sensor_values[name] = result.fragmented_payload[0]
                    else:
                        logger.debug(f"No data for {name}")

                # Build ScienceData only if we got at least some sensor values
                if sensor_values:
                    data = ScienceData(
                        temperature_celsius=sensor_values.get("temp_1"),
                        relative_humidity_percent=sensor_values.get("humidity"),
                        temperature_celsius_2=sensor_values.get("temp_2"),
                        pressure_hpa=sensor_values.get("pressure"),
                        altitude_meters=sensor_values.get("altitude"),
                        ambient_light_count=sensor_values.get("ambient_light_count"),
                        ambient_light_lux=sensor_values.get("ambient_light_lux"),
                        uv_count=sensor_values.get("uv_count"),
                        uv_index=sensor_values.get("uv_index"),
                        infrared_count=sensor_values.get("infrared_count"),
                        visible_count=sensor_values.get("visible_count"),
                        full_spectrum_count=sensor_values.get("full_spectrum_count"),
                        ir_visible_lux=sensor_values.get("ir_visible_lux"),
                        pm10_standard_ug_m3=sensor_values.get("pm10_standard"),
                        pm25_standard_ug_m3=sensor_values.get("pm25_standard"),
                        pm100_standard_ug_m3=sensor_values.get("pm100_standard"),
                        pm10_environmental_ug_m3=sensor_values.get("pm10_environmental"),
                        pm25_environmental_ug_m3=sensor_values.get("pm25_environmental"),
                        pm100_environmental_ug_m3=sensor_values.get("pm100_environmental"),
                        particulate_03um_per_01L=sensor_values.get("particulate_03um"),
                        particulate_05um_per_01L=sensor_values.get("particulate_05um"),
                        particulate_10um_per_01L=sensor_values.get("particulate_10um"),
                        particulate_25um_per_01L=sensor_values.get("particulate_25um"),
                        particulate_50um_per_01L=sensor_values.get("particulate_50um"),
                        particulate_100um_per_01L=sensor_values.get("particulate_100um"),
                        timestamp=datetime.now(),
                    )

                    # Log data to CSV
                    if True:
                        try:
                            self.data_log(data.encode_to_csv())
                        except Exception as e:
                            logger.error(f"An error occurred while logging data: {e}\n{traceback.format_exc()}")

                    # Transmit every 5th iteration
                    if counter % 5 == 0:
                        try:
                            data_header = DataHeader(
                                sender=self.get_device_id(),
                                data_type=Type.SCIENCE_DATA,
                                priority=Priority.DATA,
                            )
                            packet = Packet(data, data_header)
                            send(packet) # FIXME add later
                        except Exception as e:
                            logger.error(f"An error occurred while transmitting data: {e}\n{traceback.format_exc()}")

            except Exception as e:
                logger.error(f"Unhandled exception in CAN read loop: {e}\n{traceback.format_exc()}")

            # Sleep before next poll
            self.thread_sleep(logger, 1)

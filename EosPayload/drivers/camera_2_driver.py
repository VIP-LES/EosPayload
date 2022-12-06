from EosPayload.drivers.camera_driver import Camera1Driver
from EosLib import Device


class Camera2Driver(Camera1Driver):

    @staticmethod
    def get_device_name() -> str:
        return "camera-2-driver"

    @staticmethod
    def get_device_id() -> Device:
        return Device.CAMERA_2

    def __init__(self, output_directory: str):
        super().__init__(output_directory)
        self.camera_num = 2

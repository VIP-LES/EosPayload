# import logging
# import time
# from EosPayload.lib.driver_base import DriverBase
# # import Adafruit_BBIO.ADC as ADC
#
# #ADC.setup()
#
#
#
# # ADC
# class LightUVAUVB(DriverBase):
#
#     @staticmethod
#     def get_device_id() -> str:
#         return "Light UVA UVB"
#
#     def device_read(self, logger: logging.Logger) -> None:
#         while True:
#             # this is where you would poll a device for data or whatever
#             #value = ADC.read_raw("P9_39")
#             data = 0
#             self.data_log([str(data), str(data * data)])
#             time.sleep(3)
#
#     def device_command(self, logger: logging.Logger) -> None:
#         self.spin()
#
#     @staticmethod
#     def enabled() -> bool:
#         return False

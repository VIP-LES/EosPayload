# import logging
# import time
# from EosPayload.lib.driver_base import DriverBase
# #import Adafruit_BBIO.ADC as ADC
#
# #ADC.setup()
#
#
#
# class O3(DriverBase):
#
#     @staticmethod
#     def get_device_id() -> str:
#         return "O3"
#
#     # analog
#     def device_read(self, logger: logging.Logger) -> None:
#         while True:
#             # this is where you would poll a device for data or whatever
#             #value = ADC.read_raw("P9_37")
#             data = 0
#             self.data_log([str(data), str(data * data)])
#             time.sleep(1)
#
#     def device_command(self, logger: logging.Logger) -> None:
#         self.spin()
#
#     @staticmethod
#     def enabled() -> bool:
#         return False

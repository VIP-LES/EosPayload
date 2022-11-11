import datetime
import logging
import os
import time
import cv2

from EosPayload.lib.driver_base import DriverBase


class CameraDriver(DriverBase):

    def __init__(self):
        super().__init__()
        self.cap = None
        self.out = None
        self.path = "video/"
        self.still_capture_interval = datetime.timedelta(seconds=5)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    @staticmethod
    def get_device_id() -> str:
        return "camera-driver-002"

    def setup(self) -> None:
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 32)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 16)
        fourcc = cv2.VideoWriter_fourcc(*'YUY2')
        self.out = cv2.VideoWriter(os.path.join(self.path, 'output.avi'), fourcc, 30, (640, 480))

    def cleanup(self):
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()

    def device_read(self, logger: logging.Logger) -> None:
        frame_num = 0
        last_still_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while True:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break
                if (datetime.datetime.now() - last_still_time) > self.still_capture_interval:
                    cv2.imwrite(os.path.join(self.path, "still_image_%s.jpg") % frame_num, frame)
                    frame_num += 1
                    last_still_time = datetime.datetime.now()
                self.out.write(frame)


if __name__ == '__main__':
    cd = CameraDriver()
    print("Running setup")
    cd.setup()
    cd.cleanup()

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

        logger.info("Starting to poll for data!")
        while True:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break
                if frame_num % 200 == 0:
                    cv2.imwrite(os.path.join(self.path, "frame%s.jpg") % frame_num, frame)
                self.out.write(frame)
                #  cv2.imshow('frame', frame)
                frame_num += 1


if __name__ == '__main__':
    cd = CameraDriver()
    print("Running setup")
    cd.setup()
    cd.cleanup()

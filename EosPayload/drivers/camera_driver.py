import datetime
import logging
import os
import time

import cv2
from EosPayload.lib.base_drivers.driver_base import DriverBase


class Camera1Driver(DriverBase):

    def video_writer_setup(self):
        return cv2.VideoWriter(os.path.join(self.path, self.video_name_format.format(self.video_num)),
                               self.fourcc, self.camera_fps, self.camera_res)

    def find_next_file_num(self, filename: str) -> int:
        if filename.format(0) == filename:
            raise ValueError("Filename must be format compatible string")
        file_num = 0
        while True:
            if not os.path.exists(os.path.join(self.path, filename.format(file_num))):
                return file_num
            else:
                file_num += 1

    def __init__(self, output_directory: str, config: dict):
        super().__init__(output_directory, config)
        self.cap = None
        self.out = None
        self.path = output_directory + "/artifacts/video/"
        self.still_capture_interval = datetime.timedelta(minutes=5)
        self.video_capture_length = datetime.timedelta(minutes=1)
        self.camera_num = 0
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.camera_fps = 10
        self.camera_res = (320, 180)
        self.still_name_format = None
        self.video_name_format = None
        self.video_num = 0
        self.still_num = 0

    def setup(self) -> None:
        super().setup()
        self.register_thread('device-read', self.device_read)

        self.still_name_format = "camera-{camera}-still-image-{num}.jpg".format(camera=self.camera_num, num='{}')
        self.video_name_format = "camera-{camera}-video-{num}.avi".format(camera=self.camera_num, num='{}')
        self.video_num = self.find_next_file_num(self.video_name_format)
        self.still_num = self.find_next_file_num(self.still_name_format)

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.cap = cv2.VideoCapture(self.camera_num)
        self._logger.info(f'Setting up camera {self.camera_num}')
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 32)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 16)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_res[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_res[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, self.fourcc)
        self.out = self.video_writer_setup()
        try:
            assert self.cap.isOpened()
        except AssertionError:
            self._logger.warning(f'Unable to open camera')

        try:
            assert self.out.isOpened()
        except AssertionError:
            self._logger.warning(f'Unable to open video writer')
            raise EnvironmentError

        time.sleep(1)

    def cleanup(self):
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()

    def device_read(self, logger: logging.Logger) -> None:
        logger.info("Starting at video number {}".format(self.video_num))
        logger.info("Starting at still number {}".format(self.still_num))

        last_still_time = datetime.datetime.now()
        video_start_time = datetime.datetime.now()
        logger.info("Starting to poll for data!")
        while self.cap.isOpened():
            if (datetime.datetime.now() - video_start_time) > self.video_capture_length:
                self.video_num += 1
                logger.info("Starting video {}".format(self.video_num))
                video_start_time = datetime.datetime.now()
                self.out.release()
                self.out = self.video_writer_setup()
            self.thread_sleep(logger, 1/self.camera_fps)
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Video frame capture failed")

            if (datetime.datetime.now() - last_still_time) > self.still_capture_interval:
                cv2.imwrite(os.path.join(self.path, self.still_name_format.format(self.still_num)), frame)
                logger.info("Saving still image {}".format(self.still_num))
                self.still_num += 1
                last_still_time = datetime.datetime.now()
            self.out.write(frame)


import cv2
import threading

import modules.shared_data as shared

from config import *

class CameraThread(threading.Thread):

    def __init__(self):

        super().__init__()

        self.cap = cv2.VideoCapture(
            CAMERA_ID
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

    def run(self):

        while shared.running:

            ret, frame = self.cap.read()

            if ret:

                shared.frame = frame

    def stop(self):

        self.cap.release()
# ==========================================================
# File      : camera_thread.py
# Function  : Camera capture thread
# ==========================================================

import cv2
import threading

from config import *
import modules.shared_data as shared

# ==========================================================
# Camera capture thread
# ==========================================================

class CameraThread(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        self.daemon = True

        self.cap = cv2.VideoCapture(0)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

    # ======================================================
    # Main camera thread loop
    # ======================================================

    def run(self):

        while shared.running:

            ret, frame = self.cap.read()

            if ret:
                shared.frame = frame

    # ======================================================
    # Release camera resource
    # ======================================================

    def stop(self):

        self.cap.release()
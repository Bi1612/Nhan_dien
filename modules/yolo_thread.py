# ==========================================================
# File      : yolo_thread.py
# Function  : YOLO TensorRT inference thread
# ==========================================================

import threading
import time

import modules.shared_data as shared

from modules.detection import detect_objects

# ==========================================================
# YOLO inference thread
# ==========================================================

class YOLOThread(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        self.daemon = True

    # ======================================================
    # Main YOLO thread loop
    # ======================================================

    def run(self):

        while shared.running:

            if shared.frame is not None:

                detections = detect_objects(
                    shared.frame
                )

                shared.detections = detections

            time.sleep(0.001)
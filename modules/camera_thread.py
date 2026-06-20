import cv2
import threading

import modules.shared_data as shared
from config import *

class CameraThread(threading.Thread):

    def __init__(self):
        super().__init__()
        # Đọc tham số ID và kích thước từ file cấu hình hệ thống config của bạn
        self.cap = cv2.VideoCapture(CAMERA_ID)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.running = True

    def run(self):
        import time
        print("[INFO] Luồng Camera thu thập hình ảnh đã sẵn sàng...")
        while shared.running and self.running:
            ret, frame = self.cap.read()
            if ret:
                shared.frame = frame
            else:
                time.sleep(0.01) # Chờ nếu camera bận

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

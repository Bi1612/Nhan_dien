import threading
import cv2
import modules.shared_data as shared

class CameraThread(threading.Thread):
    def __init__(self):
        super(CameraThread, self).__init__()
        # Ép cứng cổng số 1 tương ứng với cổng USB webcam thật trên Jetson Nano
        self.cap = cv2.VideoCapture(1) 
        self.stopped = False

    def run(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                shared.frame = frame
            else:
                print("[CAMERA ERROR] Không đọc được luồng dữ liệu từ Webcam!")
            cv2.waitKey(10)

    def stop(self):
        self.stopped = True
        if self.cap.isOpened():
            self.cap.release()

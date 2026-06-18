import cv2
import threading
import modules.shared_data as shared

class CameraThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        
        # Đã cấu hình chính xác sang Index 1 theo phần cứng Jetson Nano của bạn
        self.cap = cv2.VideoCapture(1)
        
        # Cấu hình độ phân giải khung hình chuẩn cho mạng YOLOv5 TensorRT
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 416)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 416)

    def run(self):
        print("[CAMERA] Luong doc Camera USB da bat dau hoat dong.")
        while shared.running:
            ret, frame = self.cap.read()
            if not ret:
                print("[CAMERA] Canh bao: Khong the doc duoc khung hinh tu thiet bi!")
                continue
            
            # Đẩy khung hình thô vào vùng nhớ chia sẻ chung toàn cục
            shared.frame = frame

    def stop(self):
        if self.cap.is_opened():
            self.cap.release()
        print("[CAMERA] Da giai phong thiet bi camera an toan.")

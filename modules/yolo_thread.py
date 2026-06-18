import threading
import time
import cv2
import pycuda.driver as cuda # Thư viện quản lý tài nguyên GPU

import modules.shared_data as shared
from modules.detection import detect_objects

class YOLOThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        # LẤY CHÍNH XÁC ngữ cảnh CUDA đang hoạt động tại luồng chính khởi tạo mô hình
        self.ctx = cuda.Context.get_current()

    def run(self):
        # Đẩy ngữ cảnh dùng chung của luồng chính vào luồng phụ phụ trách YOLOv5
        if self.ctx:
            self.ctx.push()

        while shared.running:
            if shared.frame is None:
                time.sleep(0.01)
                continue

            start_time = time.time()
            frame = shared.frame.copy()
            frame = cv2.resize(frame, (416, 416))

            # Thực hiện suy luận nhận diện thời gian thực trên bộ nhớ an toàn
            detections = detect_objects(frame)
            shared.detections = detections

            elapsed = time.time() - start_time
            shared.yolo_fps = 1.0 / max(elapsed, 0.001)

        # Giải phóng tài nguyên khi luồng kết thúc
        if self.ctx:
            self.ctx.pop()

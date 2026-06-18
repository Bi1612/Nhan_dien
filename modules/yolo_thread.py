import threading
import time
import cv2

# Nhập thêm thư viện PyCUDA để cấu hình quản lý ngữ cảnh luồng GPU
import pycuda.driver as cuda

import modules.shared_data as shared
from modules.detection import detect_objects

class YOLOThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True
        # Tạo một bản lưu ngữ cảnh CUDA từ luồng khởi tạo chính
        self.ctx = cuda.Device(0).make_context()
        self.ctx.pop()

    def run(self):
        # Kích hoạt và đẩy ngữ cảnh CUDA vào luồng phụ này khi bắt đầu chạy
        self.ctx.push()

        while shared.running:
            if shared.frame is None:
                time.sleep(0.01)
                continue

            start_time = time.time()
            frame = shared.frame.copy()
            frame = cv2.resize(frame, (416, 416))

            # Lúc này hàm Inference sẽ chạy mượt mà trên GPU mà không bị văng lỗi Context
            detections = detect_objects(frame)
            shared.detections = detections

            elapsed = time.time() - start_time
            shared.yolo_fps = 1.0 / max(elapsed, 0.001)

        # Giải phóng ngữ cảnh CUDA khi luồng kết thúc để tránh rò rỉ bộ nhớ RAM
        self.ctx.pop()

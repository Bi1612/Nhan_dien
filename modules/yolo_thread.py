import threading
import torch
import cv2
import time
import modules.shared_data as shared

class YOLOThread(threading.Thread):
    def __init__(self):
        super(YOLOThread, self).__init__()
        self.running = True
        # Cách này không cần thư viện ultralytics, chỉ cần torch
        # Đảm bảo bồ có file 'yolov5s.pt' trong thư mục này
        try:
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.model.eval()
        except Exception as e:
            print(f"Lỗi khởi tạo model: {e}")
        
    def run(self):
        while self.running:
            if shared.frame is not None:
                frame = shared.frame.copy()
                # Chạy detect
                results = self.model(frame)
                
                # Cập nhật kết quả
                shared.detections = []
                for det in results.xyxy[0]:
                    x1, y1, x2, y2, conf, cls = det
                    if conf > 0.4: # Ngưỡng tin cậy
                        shared.detections.append({
                            "box": [x1, y1, x2, y2],
                            "class": "person" if int(cls) == 0 else "object"
                        })
                time.sleep(0.05)
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False

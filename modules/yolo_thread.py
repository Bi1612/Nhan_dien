import threading
import torch
import cv2
import time
import modules.shared_data as shared

class YOLOThread(threading.Thread):
    def __init__(self):
        super(YOLOThread, self).__init__()
        self.running = True
        # Load mô hình YOLOv5 từ bộ nhớ cache hoặc tải mới
        print("[AI ENGINE] Đang khởi tạo mô hình...")
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
        self.model.conf = 0.40  # Ngưỡng nhận diện
        
    def run(self):
        while self.running:
            if shared.frame is not None:
                # Lấy ảnh từ luồng chung
                frame = shared.frame.copy()
                
                # Chuyển hệ màu để chạy AI
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Thực hiện nhận diện
                results = self.model(img_rgb)
                
                # Trích xuất kết quả dạng bảng
                df = results.pandas().xyxy[0]
                
                detections = []
                for _, row in df.iterrows():
                    # Chỉ lọc các vật thể quan trọng cho người mù
                    if row['name'] in ["person", "car", "motorcycle", "bicycle", "bus", "truck"]:
                        detections.append({
                            "box": [row['xmin'], row['ymin'], row['xmax'], row['ymax']],
                            "class": row['name'],
                            "confidence": float(row['confidence'])
                        })
                
                # Cập nhật kết quả vào biến chung
                shared.detections = detections
                
                # Thêm khoảng nghỉ để CPU của Jetson Nano không bị quá tải
                time.sleep(0.05) 
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False

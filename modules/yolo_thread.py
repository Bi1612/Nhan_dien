import threading
import torch
import cv2
import time
import numpy as np
import modules.shared_data as shared

class YOLOThread(threading.Thread):
    def __init__(self):
        super(YOLOThread, self).__init__()
        self.running = True
        # Cách nạp mô hình "bất tử": dùng thư viện torch cơ bản
        # Bồ để file yolov5s.pt trong thư mục project là được
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.conf = 0.40
        
    def run(self):
        while self.running:
            if shared.frame is not None:
                frame = shared.frame.copy()
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Chạy inference
                results = self.model(img_rgb)
                
                # Lấy kết quả dưới dạng dataframe
                df = results.pandas().xyxy[0]
                
                detections = []
                for _, row in df.iterrows():
                    # Chỉ lọc người (person) hoặc vật cản cần thiết
                    if row['name'] in ["person", "car", "bicycle"]:
                        detections.append({
                            "box": [row['xmin'], row['ymin'], row['xmax'], row['ymax']],
                            "class": row['name'],
                            "confidence": float(row['confidence'])
                        })
                
                shared.detections = detections
                time.sleep(0.03) # Giới hạn 30FPS để không lag
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False

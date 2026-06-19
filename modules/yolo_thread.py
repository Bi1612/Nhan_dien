import threading
import torch
import cv2
import time
import modules.shared_data as shared

class YOLOThread(threading.Thread):
    def __init__(self):
        super(YOLOThread, self).__init__()
        self.running = True
        # CHẮC CHẮN KHỞI TẠO BIẾN Ở ĐÂY
        self.model = None 
        try:
            print("[AI] Đang load model...")
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.model.eval()
            print("[AI] Load model thành công!")
        except Exception as e:
            print(f"[AI] Lỗi khởi tạo model: {e}")
        
    def run(self):
        while self.running:
            # Kiểm tra self.model đã tồn tại chưa trước khi dùng
            if self.model is not None and shared.frame is not None:
                frame = shared.frame.copy()
                results = self.model(frame)
                
                shared.detections = []
                # Trích xuất kết quả
                pred_df = results.pandas().xyxy[0]
                for _, row in pred_df.iterrows():
                    if row['confidence'] > 0.4:
                        shared.detections.append({
                            "box": [row['xmin'], row['ymin'], row['xmax'], row['ymax']],
                            "class": row['name']
                        })
                time.sleep(0.05)
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False

import torch
import cv2

# Khởi tạo mô hình YOLOv5 chạy bằng PyTorch thuần ngay trên Jetson Nano
# (Bỏ qua hoàn toàn yoloDet và pycuda để không bao giờ lo thiếu file local)
print("[AI ENGINE] Đang nạp mô hình YOLOv5 chuẩn từ bộ nhớ cache...")
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
model.conf = 0.40  # Ngưỡng tin cậy nhận diện đối tượng 40%

def detect_objects(frame):
    """
    Hàm nhận diện vật cản thời gian thực.
    Trả về danh sách đối tượng đúng định dạng cấu trúc của nhóm bồ.
    """
    # Chuyển đổi hệ màu sang RGB cho mạng nơ-ron
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = model(img_rgb)
    
    # Trích xuất tọa độ dạng bảng dữ liệu pandas
    df = results.pandas().xyxy[0]
    
    detections = []
    for _, row in df.iterrows():
        cls_name = row['name']
        
        # Lọc các class gây nguy hiểm cho người khiếm thị
        if cls_name in ["person", "car", "motorcycle", "bicycle", "bus", "truck"]:
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            
            # Đóng gói cấu trúc dictionary truyền vào shared_data
            detections.append({
                "box": [x1, y1, x2, y2],
                "class": cls_name,
                "confidence": float(row['confidence'])
            })
            
    return detections

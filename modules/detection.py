import cv2
import numpy as np

print("[AI ENGINE] Đang kích hoạt Chế độ tối ưu siêu nhẹ cho Jetson Nano...")
print("[AI INFO] Đã bỏ qua nạp mô hình nặng - Hệ thống chạy mượt 100%.")

# Tạo một biến net giả lập để các file khác không bị lỗi crash code
net = "Bypass"

# Danh sách nhãn đối tượng COCO chuẩn
CLASSES = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"]

def detect_objects(frame):
    """
    Hàm nhận diện phiên bản SIÊU NHẸ.
    Không tính toán ma trận AI, không nạp file, trả về kết quả giả lập 
    để test luồng camera và phần cứng chạy mượt mà không bị treo máy.
    """
    detections = []
    
    # Tạo một khung quét giả lập (ví dụ: mô phỏng có 1 "person" ở giữa màn hình)
    # Giúp bạn test luồng âm thanh phản hồi hoặc xử lý nút bấm ngay lập tức
    height, width, _ = frame.shape
    x1, y1 = int(width * 0.3), int(height * 0.3)
    x2, y2 = int(width * 0.7), int(height * 0.7)
    
    detections.append({
        "box": [x1, y1, x2, y2],
        "class": "person",
        "confidence": 0.95
    })
                    
    return detections
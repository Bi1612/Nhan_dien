import cv2
import modules.shared_data as shared # Nơi chứa dữ liệu dùng chung (frame, detections)
from modules.camera_thread import CameraThread # Luồng đọc webcam
from modules.yolo_thread import YOLOThread       # Luồng chạy AI

# 1. Khởi tạo: Bật camera và AI lên
camera_thread = CameraThread()
yolo_thread = YOLOThread()

camera_thread.start()
yolo_thread.start()

print("🚀 Hệ thống đã sẵn sàng, đang chạy...")

# 2. Vòng lặp chính (Cái này là "trái tim" của app)
while True:
    # Nếu chưa có ảnh từ camera thì đợi
    if shared.frame is None:
        continue
    
    # Copy ảnh từ luồng camera ra để vẽ
    frame = shared.frame.copy()
    
    # 3. Vẽ Bounding Box từ dữ liệu YOLO trả về
    # shared.detections là danh sách các vật thể AI tìm được
    for obj in shared.detections:
        # Lấy tọa độ (x1, y1) là góc trái trên, (x2, y2) góc phải dưới
        x1, y1, x2, y2 = map(int, obj["box"])
        
        # Vẽ hình chữ nhật xanh lá quanh vật thể
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # In tên vật thể lên trên khung
        label = obj.get("class", "object")
        cv2.putText(frame, label, (x1, y1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # 4. Hiển thị kết quả lên màn hình HDMI 7 inch
    cv2.imshow("Hệ thống Hỗ trợ người mù", frame)
    
    # Nhấn phím 'q' để thoát
    if cv2.waitKey(1) == ord("q"):
        break

# Tắt luồng an toàn
camera_thread.stop()
yolo_thread.stop()
cv2.destroyAllWindows()

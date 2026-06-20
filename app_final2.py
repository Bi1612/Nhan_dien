import cv2
import time
import imutils
import numpy as np
import threading # Nhập thư viện đa luồng
from datetime import datetime
from yoloDet import YoloTRT

# ==========================================
# IMPORT MODULES CẢM BIẾN & DỮ LIỆU CHIA SẺ
# ==========================================
# Đảm bảo các file này nằm đúng cấu trúc thư mục modules/
try:
    from modules.sensor_thread import SensorThread
    import modules.shared_data as shared
except ImportError as e:
    print(f"Error: Không thể nhập module cảm biến. Hãy kiểm tra lại cấu trúc thư mục! Chi tiết: {e}")
    exit()

# Cờ hiệu điều khiển luồng
shared.running = True 

# ==========================================
# KÍCH HOẠT LUỒNG ĐỌC CẢM BIẾN (SERIAL)
# ==========================================
print("Đang khởi tạo luồng đọc cảm biến HC-SR04/IMU qua Serial...")
# Chú ý: Đảm bảo cổng "/dev/ttyACM0" trong file sensor_thread.py là chính xác
sensor_thread = SensorThread()
sensor_thread.start() # Khởi chạy luồng chạy ngầm

# ==========================================
# LOAD TENSORRT MODEL
# ==========================================
model = YoloTRT(
    library="yolov5/build_1/libmyplugins.so",
    engine="yolov5/build_1/yolov5n.engine",
    conf=0.5,
    yolo_ver="v5"
)

# ==========================================
# OBJECT CLASSES FOR BLIND SUPPORT
# ==========================================
OBJECT_CLASSES = [
    "person",
    "car",
    "motorcycle",
    "bus",
    "truck"
]

# ==========================================
# COLORS (Dành cho việc hiển thị debug)
# ==========================================
COLORS = {
    "person": (0, 0, 255),       # Đỏ
    "car": (255, 0, 0),          # Xanh dương
    "motorcycle": (0, 255, 255), # Vàng
    "bus": (0, 255, 0),          # Xanh lá
    "truck": (255, 0, 255)       # Tím
}

# ==========================================
# CAMERA VẬT LÝ (WEBCAM USB REAL-TIME)
# ==========================================
# Đảm bảo index (0, 1, 2) và backend V4L2 là chính xác
cap = cv2.VideoCapture(0, cv2.CAP_V4L2) 

# Độ phân giải xử lý (Giữ nguyên 416 để đảm bảo FPS cao trên Jetson)
FRAME_WIDTH = 416
FRAME_HEIGHT = 416

# Thiết lập cấu hình trực tiếp cho phần cứng Webcam USB
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Giảm lag

if not cap.isOpened():
    print("Error: Không thể kết nối với Webcam USB. Hãy kiểm tra lại cổng cắm!")
    # Dừng luồng cảm biến nếu lỗi camera
    shared.running = False
    sensor_thread.stop()
    exit()

# ==========================================
# TẠO CỬA SỔ HIỂN THỊ CÓ THỂ CO GIÃN (FULLSCREEN)
# ==========================================
WINDOW_NAME = "Blind Support AI Dashboard v1.2"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL) # Cho phép thay đổi kích thước cửa sổ

# ==========================================
# WARMUP
# ==========================================
print("Warming up TensorRT...")
ret, frame = cap.read()
if ret:
    frame = imutils.resize(frame, width=FRAME_WIDTH)
    for i in range(5):
        model.Inference(frame)
print("Warmup completed. Bắt đầu nhận diện & đo khoảng cách thực tế!")

# ==========================================
# MAIN LOOP
# ==========================================
while True:
    start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        print("Error: Mất tín hiệu từ Webcam USB!")
        break
        
    frame = imutils.resize(frame, width=FRAME_WIDTH)
    
    # ==========================================
    # LẤY DỮ LIỆU CẢM BIẾN MỚI NHẤT (TỪ SHARED DATA)
    # ==========================================
    # Giá trị này được cập nhật liên tục bởi sensor_thread chạy ngầm
    current_physical_distance = shared.distance 
    
    # ==========================================
    # YOLO DETECTION
    # ==========================================
    detections, t = model.Inference(frame)
    
    counts = {cls: 0 for cls in OBJECT_CLASSES}
    
    # Biến cờ hiệu kiểm tra nguy hiểm (Dựa trên cả Vision và Sensor)
    danger_detected = False
    
    # --- ĐIỀU KIỆN 1: CẢNH BÁO DỰA TRÊN SENSOR (KHOẢNG CÁCH THỰC TẾ) ---
    # Ví dụ: Nếu vật cản ở quá gần, dưới 50cm (ngưỡng này bạn tùy chỉnh)
    SENSOR_DANGER_THRESHOLD_CM = 50 
    if current_physical_distance < SENSOR_DANGER_THRESHOLD_CM and current_physical_distance > 1: # Tránh giá trị lỗi 0-1cm
        danger_detected = True
    
    # Ngưỡng chiều cao của Bounding Box nguy hiểm (H pixel trên tổng 416 pixel)
    CLOSE_PROXIMITY_THRESHOLD_PX = 180 
    
    # ==========================================
    # PROCESS OBJECTS & CHECK VISION DANGER
    # ==========================================
    for obj in detections:
        class_name = obj['class']
        if class_name not in OBJECT_CLASSES:
            continue
            
        x1, y1, x2, y2 = map(int, obj['box'])
        conf = float(obj['conf'])
        color = COLORS.get(class_name, (255, 255, 255))
        
        box_width = x2 - x1
        box_height = y2 - y1
        
        # --- ĐIỀU KIỆN 2: CẢNH BÁO DỰA TRÊN VISION ( bounding box to) ---
        if box_height > CLOSE_PROXIMITY_THRESHOLD_PX:
            danger_detected = True
            
        counts[class_name] += 1
        
        # Vẽ hộp nhận diện lên màn hình debug
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} H:{box_height}"
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    # ==========================================
    # HỢP NHẤT LOGIC CẢNH BÁO CHO NGƯỜI MÙ
    # ==========================================
    # Trạng thái DANGER kích hoạt nếu THỎA MÃN MỘT TRONG HAI điều kiện (Vision hoặc Sensor)
    if danger_detected:
        status = "DANGER"
        status_long = "OBSTACLE NEAR"
        status_color = (0, 0, 255)  # Màu đỏ nguy hiểm
    else:
        total_objects = sum(counts.values())
        if total_objects > 0:
            status = "CAUTION"
            status_long = "OBJECTS AHEAD"
            status_color = (0, 165, 255)  # Màu cam chú ý
        else:
            status = "CLEAR"
            status_long = "SAFE TO GO"
            status_color = (0, 255, 0)  # Màu xanh an toàn
        
    # Tính toán hiệu năng hệ thống
    end_time = time.time()
    fps = 1 / max(end_time - start_time, 0.0001)
    latency = (end_time - start_time) * 1000
        
    # ==========================================
    # [CẬP NHẬT] DEBUG DASHBOARD GỌN GÀNG (TÍCH HỢP SENSOR)
    # ==========================================
    H, W, _ = frame.shape
    
    # Vẽ panel nền đen gọn gàng (Nới rộng một chút để đủ chỗ in khoảng cách)
    cv2.rectangle(frame, (0, 0), (120, 290), (0, 0, 0), -1)
    
    panel_font_scale = 0.5
    panel_text_x = 10
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (panel_text_x, 20), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"Lat: {latency:.1f}ms", (panel_text_x, 40), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    
    # --- [MỚI] Hiển thị khoảng cách thực tế từ cảm biến HC-SR04 ---
    sensor_text_color = (255, 255, 255) # Mặc định trắng
    if current_physical_distance < SENSOR_DANGER_THRESHOLD_CM:
        sensor_text_color = (0, 0, 255) # Đỏ nếu quá gần
        
    cv2.putText(frame, f"Dist: {current_physical_distance:.1f} cm", (panel_text_x, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, sensor_text_color, 1)
    
    # Hiển thị bộ đếm chướng ngại vật di động
    cv2.putText(frame, f"P: {counts['person']}", (panel_text_x, 95), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 0, 255), 1)
    cv2.putText(frame, f"C: {counts['car']}", (panel_text_x, 115), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 0), 1)
    cv2.putText(frame, f"M: {counts['motorcycle']}", (panel_text_x, 135), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 255), 1)
    cv2.putText(frame, f"B: {counts['bus']}", (panel_text_x, 155), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"T: {counts['truck']}", (panel_text_x, 175), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 255), 1)
    
    cv2.putText(frame, "SYSTEM STATUS:", (panel_text_x, 210), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 255, 255), 1)
    cv2.putText(frame, status, (panel_text_x, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(frame, status_long, (panel_text_x, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
    
    # ==========================================
    # TIMESTAMP & SYSTEM NAME
    # ==========================================
    current_time = datetime.now().strftime("%H:%M:%S")
    W_time = W - 80 if W > 80 else 10
    cv2.putText(frame, current_time, (W_time, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    system_name = "BLIND GUIDANCE v1.2 (AI+Sens)"
    H_sys = H - 15 if H > 15 else 10
    W_sys = W - 200 if W > 200 else 10
    cv2.putText(frame, system_name, (W_sys, H_sys), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # ==========================================
    # SHOW OUTPUT
    # ==========================================
    cv2.imshow(WINDOW_NAME, frame)
    
    key = cv2.waitKey(1)
    time.sleep(0.001) # Tránh chiếm dụng 100% CPU
    
    if key == ord('f'):
        is_fullscreen = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
        if is_fullscreen == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
    if key == ord('q'):
        break

# ==========================================
# RELEASE & CLEANUP
# ==========================================
# Quan trọng: Dừng luồng cảm biến trước khi thoát
shared.running = False
sensor_thread.stop()
cap.release()
cv2.destroyAllWindows()
print("Hệ thống đã dừng an toàn.")

import cv2
import time
import imutils
import numpy as np
from datetime import datetime
from yoloDet import YoloTRT

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
# Số 0 đại diện cho Webcam USB đầu tiên kết nối vào Jetson Nano
cap = cv2.VideoCapture(0)

FRAME_WIDTH = 416
FRAME_HEIGHT = 416

# Thiết lập cấu hình trực tiếp cho phần cứng Webcam USB
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Giới hạn bộ đệm bằng 1 để giảm thiểu độ trễ hình ảnh (Lag)

# Kiểm tra xem Jetson Nano đã nhận được Webcam chưa
if not cap.isOpened():
    print("Error: Không thể kết nối với Webcam USB. Hãy kiểm tra lại cổng cắm!")
    exit()

# ==========================================
# WARMUP
# ==========================================
print("Warming up TensorRT...")
ret, frame = cap.read()
if ret:
    frame = imutils.resize(frame, width=FRAME_WIDTH)
    for i in range(5):
        model.Inference(frame)
print("Warmup completed. Bắt đầu nhận diện thực tế!")

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
    # YOLO DETECTION
    # ==========================================
    detections, t = model.Inference(frame)
    
    # Khởi tạo lại bộ đếm vật thể cho mỗi khung hình
    counts = {cls: 0 for cls in OBJECT_CLASSES}
    
    # Biến cờ hiệu kiểm tra khoảng cách nguy hiểm
    obstacle_too_close = False
    closest_obstacle_class = ""
    
    # Ngưỡng chiều cao của Bounding Box để xác định vật thể ở rất gần (đơn vị: pixel)
    CLOSE_PROXIMITY_THRESHOLD = 180 
    
    # ==========================================
    # PROCESS OBJECTS
    # ==========================================
    for obj in detections:
        class_name = obj['class']
        if class_name not in OBJECT_CLASSES:
            continue
            
        x1, y1, x2, y2 = map(int, obj['box'])
        conf = float(obj['conf'])
        color = COLORS.get(class_name, (255, 255, 255))
        
        # Tính toán kích thước của hộp nhận diện
        box_width = x2 - x1
        box_height = y2 - y1
        
        # Ước lượng khoảng cách: Hộp càng cao chứng tỏ chướng ngại vật càng gần người đi bộ
        if box_height > CLOSE_PROXIMITY_THRESHOLD:
            obstacle_too_close = True
            closest_obstacle_class = class_name
            
        counts[class_name] += 1
        
        # Vẽ hộp nhận diện lên màn hình debug
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} {conf:.2f} H:{box_height}"
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
    # SYSTEM STATUS FOR BLIND SUPPORT
    # ==========================================
    if obstacle_too_close:
        status = "DANGER - OBSTACLE NEAR"
        status_color = (0, 0, 255)  # Màu đỏ cảnh báo nguy hiểm
    else:
        total_objects = sum(counts.values())
        if total_objects > 0:
            status = "CAUTION - OBJECTS AHEAD"
            status_color = (0, 165, 255)  # Màu cam chú ý
        else:
            status = "CLEAR - SAFE TO GO"
            status_color = (0, 255, 0)  # Màu xanh an toàn
        
    # Tính toán hiệu năng hệ thống
    end_time = time.time()
    fps = 1 / max(end_time - start_time, 0.0001)
    latency = (end_time - start_time) * 1000
        
    # ==========================================
    # DEBUG DASHBOARD
    # ==========================================
    cv2.rectangle(frame, (0, 0), (280, 280), (0, 0, 0), -1)
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Latency: {latency:.1f} ms", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.putText(frame, f"Cars: {counts['car']}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, f"Persons: {counts['person']}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, f"Motorcycles: {counts['motorcycle']}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    cv2.putText(frame, "SYSTEM STATUS:", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, status, (20, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    # ==========================================
    # TIMESTAMP & SYSTEM NAME
    # ==========================================
    current_time = datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, current_time, (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "BLIND GUIDANCE SYS", (120, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # ==========================================
    # SHOW OUTPUT
    # ==========================================
    cv2.imshow("Blind Support AI Dashboard", frame)
    
    key = cv2.waitKey(1)
    time.sleep(0.001)
    
    if key == ord('q'):
        break

# ==========================================
# RELEASE
# ==========================================
cap.release()
cv2.destroyAllWindows()

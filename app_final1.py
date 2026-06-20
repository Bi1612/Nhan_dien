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
# Nếu Bước 3 trước đó bạn tìm ra số index khác 0, hãy thay số 0 ở đây
cap = cv2.VideoCapture(0, cv2.CAP_V4L2) 

# Độ phân giải xử lý (Giữ nguyên 416 để đảm bảo FPS cao trên Jetson)
FRAME_WIDTH = 416
FRAME_HEIGHT = 416

# Thiết lập cấu hình trực tiếp cho phần cứng Webcam USB
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Error: Không thể kết nối với Webcam USB. Hãy kiểm tra lại index (0, 1, 2)!")
    exit()

# ==========================================
# [MỚI] TẠO CỬA SỔ HIỂN THỊ CÓ THỂ CO GIÃN (FULLSCREEN)
# ==========================================
WINDOW_NAME = "Blind Support AI Dashboard"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL) # Cho phép thay đổi kích thước cửa sổ
# cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # Bật dòng này nếu muốn mặc định mở là Fullscreen

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
    
    counts = {cls: 0 for cls in OBJECT_CLASSES}
    obstacle_too_close = False
    closest_obstacle_class = ""
    
    # Ngưỡng chiều cao của Bounding Box nguy hiểm (H pixel trên tổng 416 pixel)
    # Bạn có thể nhìn thông số H:xx in trên màn hình để điều chỉnh số này
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
        
        box_width = x2 - x1
        box_height = y2 - y1
        
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
    # [TỐI ƯU] DEBUG DASHBOARD GỌN GÀNG (TÍNH TOÁN THEO TỶ LỆ %)
    # ==========================================
    H, W, _ = frame.shape
    
    # Vẽ panel nền đen gọn gàng vừa vặn với text (Khoảng 20% width khung hình)
    cv2.rectangle(frame, (0, 0), (100, 260), (0, 0, 0), -1)
    
    panel_font_scale = 0.5
    panel_text_x = 10
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (panel_text_x, 20), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"Lat: {latency:.1f}ms", (panel_text_x, 40), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    
    cv2.putText(frame, f"P: {counts['person']}", (panel_text_x, 70), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 0, 255), 1)
    cv2.putText(frame, f"C: {counts['car']}", (panel_text_x, 90), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 0), 1)
    cv2.putText(frame, f"M: {counts['motorcycle']}", (panel_text_x, 110), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 255), 1)
    cv2.putText(frame, f"B: {counts['bus']}", (panel_text_x, 130), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"T: {counts['truck']}", (panel_text_x, 150), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 255), 1)
    
    cv2.putText(frame, "STATUS:", (panel_text_x, 185), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 255, 255), 1)
    cv2.putText(frame, status, (panel_text_x, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    cv2.putText(frame, status_long, (panel_text_x, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
    
    # ==========================================
    # [MỚI] TIMESTAMP & SYSTEM NAME GỌN GÀNG (TÍNH TOÁN THEO TỶ LỆ %)
    # ==========================================
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Đặt timestamp góc trên bên phải
    time_font_scale = 0.5
    cv2.putText(frame, current_time, (W - 80, 20), cv2.FONT_HERSHEY_SIMPLEX, time_font_scale, (255, 255, 255), 1)
    
    # Đặt tên hệ thống gọn gàng ở góc dưới bên phải
    system_name = "BLIND GUIDANCE SYS v1.1"
    cv2.putText(frame, system_name, (W - 180, H - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # ==========================================
    # SHOW OUTPUT (Giờ đây cửa sổ có thể co giãn bằng chuột)
    # ==========================================
    cv2.imshow(WINDOW_NAME, frame)
    
    key = cv2.waitKey(1)
    time.sleep(0.001)
    
    # Nhấn 'f' để bật/tắt chế độ Fullscreen bằng phím tắt
    if key == ord('f'):
        is_fullscreen = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
        if is_fullscreen == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
    if key == ord('q'):
        break

# ==========================================
# RELEASE
# ==========================================
cap.release()
cv2.destroyAllWindows()

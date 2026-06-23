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
try:
    from modules.sensor_thread import SensorThread
    from modules.gps_thread import GPSThread        # <-- ĐỒNG BỘ FILE GPS CHỐT
    import modules.shared_data as shared
    # Import module âm thanh chạy ngầm đã tối ưu của Bi
    from modules.audio_alert import play_voice_alert
except ImportError as e:
    print(f"Error: Không thể nhập module cảm biến/âm thanh. Hãy kiểm tra lại cấu trúc thư mục! Chi tiết: {e}")
    exit()

# Cờ hiệu điều khiển luồng
shared.running = True 

# ==========================================
# KÍCH HOẠT CÁC LUỒNG ĐỌC PHẦN CỨNG (CHẠY NGẦM)
# ==========================================
print("Đang khởi tạo luồng đọc cảm biến HC-SR04/IMU qua Serial...")
sensor_thread = SensorThread()
sensor_thread.start() 

print("Đang khởi tạo luồng đọc dữ liệu GPS...")
gps_thread = GPSThread()                            # <-- KHỞI CHẠY LUỒNG GPS MỚI CỦA BI
gps_thread.start()

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
cap = cv2.VideoCapture(0, cv2.CAP_V4L2) 

# Độ phân giải xử lý chuẩn hóa để giảm lag
FRAME_WIDTH = 416
FRAME_HEIGHT = 416

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Đặt bộ đệm bằng 1 để triệt tiêu độ trễ tích lũy

if not cap.isOpened():
    print("Error: Không thể kết nối với Webcam USB. Hãy kiểm tra lại cổng cắm!")
    shared.running = False
    sensor_thread.stop()
    gps_thread.stop()
    exit()

# ==========================================
# TẠO CỬA SỔ HIỂN THỊ CÓ THỂ CO GIÃN (FULLSCREEN)
# ==========================================
WINDOW_NAME = "Blind Support AI Dashboard v1.2"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

# ==========================================
# WARMUP MÔ HÌNH TENSORRT CHỐT LAG KHỞI ĐỘNG
# ==========================================
print("Warming up TensorRT...")
ret, frame = cap.read()
if ret:
    frame = imutils.resize(frame, width=FRAME_WIDTH)
    for i in range(5):
        model.Inference(frame)
print("Warmup completed. Bắt đầu nhận diện & đo khoảng cách thực tế!")

# ==========================================
# CẤU HÌNH HÌNH HỌC CAMERA (GÓC NHÌN THEO CÔ THẢO)
# ==========================================
FOV_HORIZONTAL = 60          # Góc nhìn ngang mặc định của Webcam (~60 độ)
FRAME_CENTER_X = 208         # Tâm trục X màn hình (416 / 2)
last_audio_time = 0

# ==========================================
# MAIN LOOP (VÒNG LẶP XỬ LÝ CHÍNH THỜI GIAN THỰC)
# ==========================================
while True:
    start_time = time.time()
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("[Warning] Mất khung hình từ Webcam, đang thử kết nối lại...")
        # Tạo màn hình đen thông báo lỗi tạm thời chống sập giao diện khi sụt áp cổng USB
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        cv2.putText(frame, "RECONNECTING CAMERA...", (50, 208), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow(WINDOW_NAME, frame)
        cv2.waitKey(10)
        time.sleep(0.1) # Chờ 100ms cho ổn định lại điện áp cổng USB
        continue        # Quay đầu vòng lặp đọc lại frame mới chứ không văng ứng dụng
   
    frame = imutils.resize(frame, width=FRAME_WIDTH)
    current_time = time.time() 
    
    # Lấy dữ liệu khoảng cách mới nhất từ luồng Arduino ngầm
    current_physical_distance = shared.distance 
    
    # Thực hiện Inference nhận diện vật thể bằng mạng YOLOv5 TensorRT
    detections, t = model.Inference(frame)
    counts = {cls: 0 for cls in OBJECT_CLASSES}
    danger_detected = False
    
    # --- ĐIỀU KIỆN 1: CẢNH BÁO DỰA TRÊN CẢM BIẾN SIÊU ÂM ---
    SENSOR_DANGER_THRESHOLD_CM = 50 
    if current_physical_distance < SENSOR_DANGER_THRESHOLD_CM and current_physical_distance > 1:
        danger_detected = True
        
    # SỬA LỖI TREO CẢM BIẾN ĐỘT NGỘT (BÁO 999): Ước lượng khoảng cách bằng hộp bao Camera
    if (current_physical_distance == 999.0 or current_physical_distance is None) and len(detections) > 0:
        first_obj = detections[0]
        _, y1_f, _, y2_f = map(int, first_obj['box'])
        # Thuật toán bù dữ liệu bằng mô hình lỗ kim hình học camera
        current_physical_distance = (180 / max(y2_f - y1_f, 1)) * 150.0
    
    # Ngưỡng chiều cao nguy hiểm của Bounding Box (Vật cản quá to sát mắt camera)
    CLOSE_PROXIMITY_THRESHOLD_PX = 180 
    detected_objects_info = []
    
    # ==========================================
    # QUÉT VẬT THỂ & TÍNH TOÁN LƯỢNG GIÁC PHƯƠNG VỊ
    # ==========================================
    for obj in detections:
        class_name = obj['class']
        if class_name not in OBJECT_CLASSES:
            continue
            
        x1, y1, x2, y2 = map(int, obj['box'])
        color = COLORS.get(class_name, (255, 255, 255))
        box_height = y2 - y1
        
        # --- THUẬT TOÁN Ý TƯỞNG CỦA CÔ THẢO: TÍNH GÓC LỆCH BETA PHƯƠNG VỊ ---
        x_center = (x1 + x2) / 2
        beta_angle = ((x_center - FRAME_CENTER_X) / FRAME_CENTER_X) * (FOV_HORIZONTAL / 2)
        
        # Phân vùng hướng không gian dựa trên ranh giới quyết định góc Beta
        if beta_angle > 8:
            direction_text = "ben phai"
        elif beta_angle < -8:
            direction_text = "ben trai"
        else:
            direction_text = "chinh dien"
            
        # Lưu thông tin phục vụ phát âm thanh thính giác hướng
        detected_objects_info.append({"class": class_name, "direction": direction_text})
        
        # --- ĐIỀU KIỆN 2: CẢNH BÁO NGUY HIỂM BẰNG ĐỘ LỚN HỘP BAO (VISION) ---
        if box_height > CLOSE_PROXIMITY_THRESHOLD_PX:
            danger_detected = True
            
        counts[class_name] += 1
        
        # Vẽ khung và nhãn chứa thông số chiều cao H và góc lệch Beta lên màn hình debug
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} H:{box_height} B:{int(beta_angle)}deg"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # ==========================================
    # HỢP NHẤT LOGIC CẢNH BÁO VÀ PHÁT LOA THOẠI HƯỚNG KHÔNG GIAN
    # ==========================================
    if danger_detected:
        status = "DANGER"
        status_long = "OBSTACLE NEAR"
        status_color = (0, 0, 255) # Màu đỏ cảnh báo
        
        # Khống chế thời gian spam âm thanh khẩn cấp (3 giây/lần)
        if current_time - last_audio_time > 3:
            play_voice_alert("Nguy hiểm. Dừng lại.")
            last_audio_time = current_time
    else:
        total_objects = sum(counts.values())
        if total_objects > 0:
            status = "CAUTION"
            status_long = "OBJECTS AHEAD"
            status_color = (0, 165, 255) # Màu cam chú ý
            
            # Khống chế thời gian spam âm thanh chú ý hướng (5 giây/lần)
            if current_time - last_audio_time > 5:
                if len(detected_objects_info) > 0:
                    first_item = detected_objects_info[0]
                    dict_vi = {"person": "người", "car": "ô tô", "motorcycle": "xe máy", "bus": "xe buýt", "truck": "xe tải"}
                    obj_vi = dict_vi.get(first_item["class"], "vật cản")
                    dir_vi = first_item["direction"]
                    
                    # Phát cảnh báo âm thanh kết hợp phân vùng hướng thông minh
                    play_voice_alert(f"Chú ý. Có {obj_vi} {dir_vi}.")
                else:
                    play_voice_alert("Chú ý. Phía trước có vật cản.")
                last_audio_time = current_time
        else:
            status = "CLEAR"
            status_long = "SAFE TO GO"
            status_color = (0, 255, 0) # Màu xanh an toàn
        
    # Đo lường hiệu năng xử lý tại biên của Jetson Nano
    end_time = time.time()
    fps = 1 / max(end_time - start_time, 0.0001)
    latency = (end_time - start_time) * 1000
        
    # ==========================================
    # PANEL DASHBOARD HIỂN THỊ (TÍCH HỢP HỢP NHẤT SENSOR + GPS)
    # ==========================================
    H, W, _ = frame.shape
    # Thiết lập hộp Dashboard màu đen (Nới rộng lên kích thước 150x360 để chứa vừa vặn thông tin GPS)
    cv2.rectangle(frame, (0, 0), (150, 360), (0, 0, 0), -1)
    
    panel_font_scale = 0.45
    panel_text_x = 10
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (panel_text_x, 20), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"Lat: {latency:.1f}ms", (panel_text_x, 40), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    
    sensor_text_color = (0, 0, 255) if current_physical_distance < SENSOR_DANGER_THRESHOLD_CM else (255, 255, 255)
    cv2.putText(frame, f"Dist: {current_physical_distance:.1f} cm", (panel_text_x, 65), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, sensor_text_color, 1)
    
    # --- ĐOẠN ĐỒ HỌA IN THÔNG SỐ GPS LÊN DASHBOARD ---
    if shared.gps_valid:
        cv2.putText(frame, f"GPS: OK ({shared.gps_speed:.1f} km/h)", (panel_text_x, 90), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
        cv2.putText(frame, f"LAT: {shared.latitude:.4f}", (panel_text_x, 110), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 255, 0), 1)
        cv2.putText(frame, f"LON: {shared.longitude:.4f}", (panel_text_x, 130), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 255, 0), 1)
    else:
        cv2.putText(frame, "GPS: FIXING...", (panel_text_x, 90), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 0, 255), 1)
    
    # Đẩy vị trí hiển thị các đối tượng nhận diện xuống dưới nhường chỗ cho GPS
    cv2.putText(frame, f"P: {counts['person']}", (panel_text_x, 160), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 0, 255), 1)
    cv2.putText(frame, f"C: {counts['car']}", (panel_text_x, 180), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 0), 1)
    cv2.putText(frame, f"M: {counts['motorcycle']}", (panel_text_x, 200), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 255), 1)
    cv2.putText(frame, f"B: {counts['bus']}", (panel_text_x, 220), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (0, 255, 0), 1)
    cv2.putText(frame, f"T: {counts['truck']}", (panel_text_x, 240), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 0, 255), 1)
    
    cv2.putText(frame, "SYSTEM STATUS:", (panel_text_x, 280), cv2.FONT_HERSHEY_SIMPLEX, panel_font_scale, (255, 255, 255), 1)
    cv2.putText(frame, status, (panel_text_x, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(frame, status_long, (panel_text_x, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
    
    # ==========================================
    # TIMESTAMP THỜI GIAN THỰC & TÊN HỆ THỐNG
    # ==========================================
    current_time_str = datetime.now().strftime("%H:%M:%S")
    W_time = W - 80 if W > 80 else 10
    cv2.putText(frame, current_time_str, (W_time, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    system_name = "BLIND GUIDANCE v1.2 (AI+Sens)"
    H_sys = H - 15 if H > 15 else 10
    W_sys = W - 200 if W > 200 else 10
    cv2.putText(frame, system_name, (W_sys, H_sys), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # ==========================================
    # HIỂN THỊ GIAO DIỆN RA MÀN HÌNH HỘI ĐỒNG
    # ==========================================
    cv2.imshow(WINDOW_NAME, frame)
    key = cv2.waitKey(1)
    
    # GIẢI PHÁP ĐẶC TRỊ LỖI ĐƠ LAG MÁY: Nâng từ 0.005 lên 0.03 (Nghỉ 30ms) 
    # Giúp hạ nhiệt CPU, giải phóng băng thông đồ họa, hệ thống chạy siêu mát mượt!
    time.sleep(0.03) 
    
    if key == ord('f'): # Phím tắt F bật tắt chế độ Toàn màn hình (Fullscreen)
        is_fullscreen = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
        if is_fullscreen == cv2.WINDOW_FULLSCREEN:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        else:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
    if key == ord('q'): # Phím tắt Q tắt ứng dụng an toàn
        break

# ==========================================
# GIẢI PHÓNG TÀI NGUYÊN & ĐÓNG AN TOÀN HỆ THỐNG
# ==========================================
shared.running = False
sensor_thread.stop()
gps_thread.stop()       # <-- NGẮT LUỒNG GPS AN TOÀN KHI THOÁT APP
cap.release()
cv2.destroyAllWindows()
print("Hệ thống đã dừng an toàn.")

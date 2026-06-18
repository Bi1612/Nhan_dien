import cv2
import time

# Hằng số hiệu chuẩn hệ thống lượng giác 4 mét hỗ trợ người khiếm thị
FOCAL_LENGTH = 350       # Tiêu cự camera (Đơn vị: Pixel - Sẽ căn chỉnh lại nếu cần)
REAL_HEIGHT_PERSON = 1.6 # Chiều cao thực tế trung bình của đối tượng (mét)

# Biến lưu vết lịch sử khoảng cách phục vụ bài toán bước tiến 2 mét của cô giáo
history_dist = None

def estimate_distance_and_angle(obj, im_width=416):
    """Tính toán khoảng cách toán học (m) và góc lệch (độ) từ khung Bounding Box"""
    x1, y1, x2, y2 = map(int, obj["box"])
    h_pixel = max(y2 - y1, 1) # Tránh lỗi chia cho 0
    x_center = (x1 + x2) / 2
    
    # Công thức tỷ lệ nghịch hình học máy tính đơn mắt (Monocular Distance)
    distance_cam = (FOCAL_LENGTH * REAL_HEIGHT_PERSON) / h_pixel
    # Tính góc lệch tâm so với trục đối xứng thẳng camera
    angle = ((x_center - (im_width / 2)) / FOCAL_LENGTH) * 57.2958
    return distance_cam, angle

def check_forward_collision(detections, zone, speed_kmh, distance_sonar_cm):
    """
    Hàm xử lý Sensor Fusion cốt lõi cho người đi bộ khiếm thị:
    1. Loại bỏ điều kiện bắt buộc tốc độ xe ô tô di chuyển.
    2. Bắt kịch bản di chuyển 2 mét để phân loại trạng thái Vật cản Tĩnh / Động.
    """
    global history_dist
    
    if not detections:
        history_dist = None
        return "SAFE"

    # Chuyển đổi dữ liệu siêu âm Arduino từ cm sang mét
    distance_sonar_m = distance_sonar_cm / 100.0

    for obj in detections:
        cls = obj["class"]
        
        # Chỉ quét các nhóm vật cản gây cản trở lối đi
        if cls not in ["person", "car", "truck", "bus", "motorcycle"]:
            continue

        # Trích xuất cự ly hình học từ khung pixel camera
        distance_cam, angle = estimate_distance_and_angle(obj, im_width=416)
        
        # Chỉ xử lý khi vật thể lọt vào tầm hoạt động an toàn dưới 4.0 mét
        if distance_cam <= 4.0:
            
            # KIỂM TRA BÀI TOÁN CỦA CÔ GIÁO:
            # Nếu trước đó hệ thống đã từng lưu vết vật cản xuất hiện ở vùng biên ~4 mét
            if history_dist is not None and (3.7 <= history_dist <= 4.3):
                # Người mù chủ động bước tiến về phía trước 2 mét
                # Khoảng cách lý thuyết mới đến vật thể nếu nó đứng im phải là:
                expected_dist = history_dist - 2.0 
                
                # Kết hợp cảm biến trung bình trọng số giữa Camera và Siêu âm Arduino
                current_real_dist = (distance_cam + distance_sonar_m) / 2.0
                
                # Kiểm tra sai số lệch ngưỡng cho phép vật thể tĩnh cố định (0.35m)
                if abs(current_real_dist - expected_dist) <= 0.35:
                    print(f"[LOG] Phat hien vat can TINH co dinh tai: {current_real_dist:.1f}m.")
                    return "DANGER" # Trả về Danger để kích hoạt còi kêu liên tục
                else:
                    print(f"[LOG] Phat hien doi tuong DONG dang di chuyen cat ngang vỉa hè.")
                    return "WARNING" # Vật cản động đang tự di chuyển né tránh
            else:
                # Ghi nhận mục tiêu lọt vào vùng biên quét 4 mét lần đầu tiên để theo dõi chu kỳ sau
                history_dist = distance_cam
                print(f"[LOG] Muc tieu vao vung bien 4m: goc {angle:.1f} do")
                return "WARNING"

    return "SAFE"

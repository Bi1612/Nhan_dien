import cv2
import time

# Hằng số cấu hình hệ thống lượng giác 4 mét hỗ trợ người khiếm thị
FOCAL_LENGTH = 350       # Tiêu cự camera hành trình sau khi hiệu chuẩn (Calibration)
REAL_HEIGHT_PERSON = 1.6 # Chiều cao thực tế trung bình của đối tượng (mét)

# Biến toàn cục cục bộ để lưu vết lịch sử khoảng cách phục vụ bài toán của cô giáo
history_dist = None

def estimate_distance_and_angle(obj, im_width=416):
    """Tính toán khoảng cách (m) và góc lệch (độ) từ Bounding Box của YOLOv5"""
    x1, y1, x2, y2 = map(int, obj["box"])
    h_pixel = max(y2 - y1, 1) # Tránh lỗi chia cho 0
    x_center = (x1 + x2) / 2
    
    # Công thức tỷ lệ nghịch hình học máy tính
    distance_cam = (FOCAL_LENGTH * REAL_HEIGHT_PERSON) / h_pixel
    # Tính góc lệch so với trục trung tâm camera (Đổi sang độ)
    angle = ((x_center - (im_width / 2)) / FOCAL_LENGTH) * 57.2958
    return distance_cam, angle

def check_forward_collision(detections, zone, speed_kmh, distance_sonar_cm):
    """
    Hàm được kế thừa từ ADAS gốc nhưng được refactor lại toàn diện:
    1. Bỏ hoàn toàn ràng buộc tốc độ xe di chuyển.
    2. Thực hiện kết hợp cảm biến (Sensor Fusion) đo cự ly và phân biệt vật thể Tĩnh / Động.
    """
    global history_dist
    
    if not detections:
        # Nếu không có vật thể, reset lại lịch sử theo dõi
        history_dist = None
        return "SAFE"

    # Đổi dữ liệu siêu âm Arduino từ cm sang mét
    distance_sonar_m = distance_sonar_cm / 100.0

    for obj in detections:
        cls = obj["class"]
        
        # Chỉ nhận diện các class vật cản gây nguy hiểm cho người đi bộ
        if cls not in ["person", "car", "truck", "bus", "motorcycle"]:
            continue

        # Trích xuất khoảng cách và góc lệch toán học từ camera hành trình
        distance_cam, angle = estimate_distance_and_angle(obj, im_width=416)
        
        # Chỉ xử lý trong phạm vi tối đa 4 mét (Giới hạn hoạt động ổn định của siêu âm)
        if distance_cam <= 4.0:
            
            # KIỂM TRA BÀI TOÁN CỦA CÔ GIÁO:
            # Nếu trước đó hệ thống đã từng ghi nhận vật thể xuất hiện ở vùng biên ~4 mét
            if history_dist is not None and (3.7 <= history_dist <= 4.3):
                # Kịch bản: Người mù chủ động bước tiến về phía trước 2 mét
                # Khoảng cách lý thuyết mới đến vật thể nếu nó đứng im cố định phải là 2 mét
                expected_dist = history_dist - 2.0 
                
                # Tính toán cự ly thực tế tích hợp từ hai cảm biến (Sensor Fusion)
                current_real_dist = (distance_cam + distance_sonar_m) / 2.0
                
                # Kiểm tra sai số lệch ngưỡng cho phép 0.35 mét
                if abs(current_real_dist - expected_dist) <= 0.35:
                    print(f"[LOG] Vat can TINH o goc {angle:.1f} do, cach {current_real_dist:.1f}m.")
                    return "DANGER" # Gửi tín hiệu nguy hiểm vật cản tĩnh cản lối đi
                else:
                    print(f"[LOG] Vat can DONG o goc {angle:.1f} do dang di chuyen.")
                    return "WARNING" # Vật thể động đang di chuyển né tránh vỉa hè
            else:
                # Lưu vết lịch sử khi vật thể lọt vào vùng biên 4 mét lần đầu tiên
                history_dist = distance_cam
                print(f"[LOG] Muc tieu vao vung bien 4m: goc {angle:.1f} do")
                return "WARNING"

    return "SAFE"

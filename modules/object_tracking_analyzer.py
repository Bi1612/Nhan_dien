# modules/object_tracker_analyzer.py
import math
import time

class ObjectAnalyzer:
    def __init__(self):
        # Lưu trữ trạng thái vật thể: {track_id: {"first_d":, "moved_dist":, "last_time":}}
        self.tracked_objects = {} 
        self.fov_horizontal = 60.0 # Cấu hình tùy theo Camera của bạn
        self.image_width = 640     # Cấu hình theo độ phân giải frame

    def calculate_angle(self, bbox_x_center):
        # Tính góc lệch alpha so với tâm trục chính của xe
        center_img = self.image_width / 2
        angle = (bbox_x_center - center_img) * (self.fov_horizontal / self.image_width)
        return angle # Đơn vị: Độ (Âm là bên trái, Dương là bên phải)

    def update_and_check(self, current_detections, current_distance, gps_speed):
        """
        current_detections: Danh sách các đối tượng từ YOLO gồm [x_center, y_center, track_id, class_name]
        current_distance: Khoảng cách từ cảm biến siêu âm (cm hoặc m)
        gps_speed: Vận tốc xe từ GPS (m/s)
        """
        current_time = time.time()
        
        for det in current_detections:
            x_c, y_c, track_id, label = det
            angle = self.calculate_angle(x_c)
            
            # Giả định nếu vật thể nằm ở chính diện (góc nhỏ), lấy khoảng cách từ cảm biến siêu âm
            # Nếu lệch biên, có thể ước lượng khoảng cách từ kích thước bbox (nâng cao)
            d_current = current_distance / 100.0 # Đổi sang mét
            
            if track_id not in self.tracked_objects:
                # Bước 1: Nhận diện đối tượng lần đầu (ví dụ quanh mốc ~ 5 mét như cô nói)
                if 4.5 <= d_current <= 5.5:
                    self.tracked_objects[track_id] = {
                        "first_distance": d_current,
                        "first_angle": angle,
                        "accumulated_car_travel": 0.0,
                        "last_time": current_time,
                        "status": "INITIALIZED"
                    }
            else:
                # Bước 2: Vật thể đã được lưu, tính quãng đường xe mình đã đi được (Delta s)
                obj = self.tracked_objects[track_id]
                dt = current_time - obj["last_time"]
                delta_s = gps_speed * dt # Quãng đường xe mình đi được trong dt giây
                obj["accumulated_car_travel"] += delta_s
                obj["last_time"] = current_time
                
                # Bước 3: Khi xe mình đi được thêm cỡ 2 mét (sai số trong khoảng 1.8m - 2.2m)
                if 1.8 <= obj["accumulated_car_travel"] <= 2.2 and obj["status"] == "INITIALIZED":
                    expected_distance = obj["first_distance"] - obj["accumulated_car_travel"]
                    
                    # So sánh khoảng cách đo thực tế d_current với khoảng cách lý thuyết expected_distance
                    if abs(d_current - expected_distance) < 0.4: # Sai số cho phép 40cm
                        obj["status"] = "STATIC_OBSTACLE" #(Vật cản tĩnh)
                    else:
                        obj["status"] = "DYNAMIC_OBJECT" #(Vật thể di động)
                        
        return self.tracked_objects

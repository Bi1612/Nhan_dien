# modules/object_tracking_analyzer.py
import time

class BlindAssistantAnalyzer:
    def __init__(self):
        self.tracked_obstacles = {}
        self.fov_horizontal = 70.0  # Góc quét camera hành trình đeo ngực/kính
        self.image_width = 640
        self.walking_speed = 1.1    # Tốc độ đi bộ mặc định của người (1.1 m/s)

    def get_direction_label(self, angle):
        """Chuyển đổi góc alpha sang khẩu lệnh hướng"""
        if angle < -15: return "Bên trái"
        elif angle > 15: return "Bên phải"
        return "Chính diện"

    def process_pedestrian_movement(self, detections, current_distance_cm):
        current_time = time.time()
        d_current_m = current_distance_cm / 100.0  # Khoảng cách mét từ siêu âm

        # 1. Cập nhật ước lượng quãng đường người mù đã đi bộ (Delta s)
        for track_id, data in list(self.tracked_obstacles.items()):
            dt = current_time - data["last_time"]
            delta_s = self.walking_speed * dt
            data["distance_walked"] += delta_s
            data["last_time"] = current_time
            
            if current_time - data["last_seen"] > 1.5:
                del self.tracked_obstacles[track_id]

        # 2. Phân tích vật cản từ YOLO dữ liệu người mù
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            track_id = det.get("track_id", None)
            cls_name = det["class"]

            if track_id is None: continue

            x_center = (x1 + x2) / 2.0
            # Góc alpha lệch so với hướng mặt người mù
            angle = (x_center - (self.image_width / 2.0)) * (self.fov_horizontal / self.image_width)
            direction = self.get_direction_label(angle)

            if track_id not in self.tracked_obstacles:
                # Thiết lập mốc bắt đầu nhận diện vật cản ở tầm xa an toàn (ví dụ: ~3 mét)
                if 2.5 <= d_current_m <= 3.5:
                    self.tracked_obstacles[track_id] = {
                        "class": cls_name,
                        "initial_dist": d_current_m,
                        "direction": direction,
                        "distance_walked": 0.0,
                        "last_time": current_time,
                        "last_seen": current_time,
                        "status": "TRACKING"
                    }
            else:
                obj = self.tracked_obstacles[track_id]
                obj["last_seen"] = current_time
                
                # Logic kiểm tra sau khi người mù đã đi tiếp được khoảng 1.5 mét
                if 1.3 <= obj["distance_walked"] <= 1.7 and obj["status"] == "TRACKING":
                    expected_dist = obj["initial_dist"] - obj["distance_walked"]
                    
                    # So sánh thực tế và lý thuyết
                    if abs(d_current_m - expected_dist) < 0.35: # sai số 35cm
                        obj["status"] = "STATIC"  # Vật cản tĩnh (vỉa hè, cây, tường)
                        obj["alert_phrase"] = f"Phát hiện {obj['class']} cố định, {direction}."
                    else:
                        obj["status"] = "DYNAMIC" # Vật cản động (người, xe di chuyển)
                        obj["alert_phrase"] = f"Cảnh báo có {obj['class']} di động, {direction}."
                        
        return self.tracked_obstacles

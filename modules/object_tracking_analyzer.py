# ==============================================================================
# PHÂN HỆ THEO DÕI VÀ PHÂN TÍCH ĐỘNG HỌC VẬT CẢN CHO NGƯỜI MÙ
# ==============================================================================
# Tệp tin: object_tracking_analyzer.py
# ==============================================================================



class BlindAssistantAnalyzer:
    def __init__(self):
        self.tracked_obstacles = {}
        self.fov_horizontal = 70.0  # Góc quét camera
        self.image_width = 640
        self.walking_speed = 1.1    # Tốc độ đi bộ mặc định (1.1 m/s)

    def get_direction_label(self, angle):
        if angle < -15: return "Ben trai"
        elif angle > 15: return "Ben phai"
        return "Chinh dien"

    def process_pedestrian_movement(self, detections, current_distance_cm):
        import time
        current_time = time.time()
        d_current_m = current_distance_cm / 100.0  # Đổi sang mét

        # 1. Cập nhật ước lượng quãng đường người mù đã đi bộ (Delta s)
        for track_id, data in list(self.tracked_obstacles.items()):
            dt = current_time - data["last_time"]
            delta_s = self.walking_speed * dt
            data["distance_walked"] += delta_s
            data["last_time"] = current_time
            
            if current_time - data["last_seen"] > 1.5:
                del self.tracked_obstacles[track_id]

        # 2. Phân tích vật cản từ dữ liệu YOLO
        for det in detections:
            if isinstance(det, dict):
                x1, y1, x2, y2 = det["box"]
                track_id = det.get("track_id", None)
                cls_name = det["class"]
            else:
                x1, y1, x2, y2 = map(float, det.xyxy[0].cpu().numpy())
                track_id = int(det.id[0].item()) if det.id is not None else None
                cls_name = str(det.cls[0].item())

            if track_id is None: 
                continue

            x_center = (x1 + x2) / 2.0
            angle = (x_center - (self.image_width / 2.0)) * (self.fov_horizontal / self.image_width)
            direction = self.get_direction_label(angle)

            if track_id not in self.tracked_obstacles:
                # Bắt đầu theo dõi ở tầm xa an toàn (khoảng 2.5m - 3.5m)
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
                obj["current_angle"] = angle
                
                # Logic kiểm tra sau khi người mù đã đi tiếp được khoảng 1.5 mét
                if 1.3 <= obj["distance_walked"] <= 1.7 and obj["status"] == "TRACKING":
                    expected_dist = obj["initial_dist"] - obj["distance_walked"]
                    
                    # So sánh khoảng cách thực tế và khoảng cách lý thuyết
                    if abs(d_current_m - expected_dist) < 0.35:
                        obj["status"] = "STATIC"  
                        obj["alert_phrase"] = f"Phat hien {obj['class']} co dinh, {direction}."
                    else:
                        obj["status"] = "DYNAMIC" 
                        obj["alert_phrase"] = f"Canh bao co {obj['class']} di dong, {direction}."
                        
        return self.tracked_obstacles

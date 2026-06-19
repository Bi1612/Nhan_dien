import threading
import time
import cv2

import modules.shared_data as shared
# Giữ nguyên hàm gốc của bạn nếu nó phục vụ việc suy luận mô hình
from modules.detection import detect_objects 

class YOLOThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        # Bộ đếm ID thủ công nếu hàm detect_objects gốc không hỗ trợ Tracking ID
        # (Nếu hàm detect_objects của bạn dùng YOLOv8 .track(), bạn có thể lấy trực tiếp box.id)
        while shared.running:

            if shared.frame is None:
                time.sleep(0.01)
                continue

            start_time = time.time()

            frame = shared.frame.copy()

            # Giữ nguyên độ phân giải nén ảnh của hệ thống bạn
            frame = cv2.resize(
                frame,
                (416, 416)
            )

            # Gọi hàm nhận diện gốc của bạn
            raw_detections = detect_objects(frame)

            local_detections = []
            
            # Giả lập gán và duy trì Track ID dựa trên thứ tự xuất hiện hoặc cấu trúc dữ liệu dữ sẵn
            # Tinh chỉnh bọc lại cấu trúc dữ liệu để Main Loop có 'track_id' tính toán logic 2 mét
            for idx, obj in enumerate(raw_detections):
                # Ép cấu trúc dữ liệu trả về phải có trường 'track_id'
                # Nếu file detect_objects gốc của bạn đã có id thì đổi thành: track_id = obj.get("id")
                track_id = obj.get("track_id", idx + 1) 
                
                local_detections.append({
                    "box": obj["box"],       # [x1, y1, x2, y2]
                    "class": obj["class"],   # Tên nhãn (person, chair,...)
                    "track_id": track_id     # Bắt buộc phải có để nạp vào bộ tính toán của cô
                })

            # Ghi dữ liệu sạch vào bộ nhớ chia sẻ
            shared.detections = local_detections

            elapsed = time.time() - start_time
            shared.yolo_fps = 1.0 / max(elapsed, 0.001)
            
            # Nghỉ một khoảng nhỏ để mạch nhúng không bị quá nhiệt
            time.sleep(0.02)

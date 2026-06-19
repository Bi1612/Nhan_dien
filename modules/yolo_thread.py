import threading
import time
import cv2
import modules.shared_data as shared
from modules.detection import detect_objects

class YOLOThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while shared.running:
            if shared.frame is None:
                time.sleep(0.01)
                continue

            start_time = time.time()
            frame = shared.frame.copy()
            frame = cv2.resize(frame, (416, 416))

            raw_detections = detect_objects(frame)
            local_detections = []
            
            for idx, obj in enumerate(raw_detections):
                track_id = obj.get("track_id", idx + 1) 
                local_detections.append({
                    "box": obj["box"],
                    "class": obj["class"],
                    "track_id": track_id
                })

            shared.detections = local_detections
            elapsed = time.time() - start_time
            shared.yolo_fps = 1.0 / max(elapsed, 0.001)
            time.sleep(0.02)

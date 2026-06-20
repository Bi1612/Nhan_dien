# ==============================================================================
# HỆ THỐNG TRỢ GIÚP NGƯỜI MÙ - CHU KỲ XỬ LÝ TRUNG TÂM (MAIN LOOP) - FIXED
# ==============================================================================

import cv2
import time
import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.sensor_thread import SensorThread
from modules.gps_thread import GPSThread
from modules.object_tracking_analyzer import BlindAssistantAnalyzer
from modules.audio_alert import play_voice_alert

# CẤU HÌNH KIỂM TRA (DEBUG)
# Đặt thành True nếu bạn kết nối Jetson Nano với màn hình HDMI để demo cho cô xem.
# Đặt thành False nếu chạy ẩn (đeo trên người) để không bị lỗi treo hiển thị.
SHOW_GUI = True  

# Khởi kích các luồng phần cứng ngoại vi chạy song song
camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()
gps_thread = GPSThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()
gps_thread.start()

# Khởi tạo thực thể phân tích trạng thái vật cản
blind_analyzer = BlindAssistantAnalyzer()

print("[INFO] He thong ho tro nguoi mu dang chay...")

try:
    while True:
        # Cơ chế đồng bộ: Chờ luồng Camera nạp frame đầu tiên
        if shared.frame is None:
            time.sleep(0.05) # Tăng lên 50ms để giảm tải lúc khởi động
            continue

        # Sao chép dữ liệu cục bộ tránh Race Condition
        frame = shared.frame.copy()
        detections = shared.detections
        distance_cm = shared.distance

        # Nếu chưa có kết quả nhận diện nào từ YOLOThread, bỏ qua chu kỳ này để đợi
        if detections is None:
            time.sleep(0.02)
            continue

        # --------------------------------------------------------------------------
        # XỬ LÝ LOGIC THEO DÕI ĐỘNG HỌC
        # --------------------------------------------------------------------------
        tracked_obstacles = blind_analyzer.process_pedestrian_movement(
            detections=detections,
            current_distance_cm=distance_cm
        )

        # Quét trạng thái để đưa ra khẩu lệnh giọng nói kịp thời
        for track_id, obstacle in list(tracked_obstacles.items()):
            if "alert_phrase" in obstacle and obstacle["status"] in ["STATIC", "DYNAMIC"]:
                print(f"[AUDIO OUT] Đang phát lệnh thoại: {obstacle['alert_phrase']}")
                play_voice_alert(obstacle["alert_phrase"])
                del obstacle["alert_phrase"]

        # --------------------------------------------------------------------------
        # GIAO DIỆN DEBUG TRỰC QUAN HÓA (CHỈ CHẠY KHI ĐƯỢC PHÉP BẬT GUI)
        # --------------------------------------------------------------------------
        if SHOW_GUI:
            for track_id, obstacle in tracked_obstacles.items():
                for obj in detections:
                    if obj.get("track_id") == track_id:
                        x1, y1, x2, y2 = map(int, obj["box"])
                        
                        if obstacle["status"] == "STATIC":
                            color = (255, 0, 0)   # Xanh dương: Vật cản tĩnh cố định
                        elif obstacle["status"] == "DYNAMIC":
                            color = (0, 0, 255)   # Đỏ: Nguy hiểm, vật cản di động
                        else:
                            color = (0, 255, 0)   # Xanh lá: Đang trong mốc đo đạc

                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label_text = f"ID:{track_id} {obstacle['class']} [{obstacle['status']}]"
                        cv2.putText(frame, label_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        cv2.putText(frame, f"Goc: {obstacle.get('current_angle', 0):.1f} deg", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Hiển thị thông số khoảng cách lên góc màn hình
            cv2.putText(frame, f"Sieu am DIST: {distance_cm:.1f} cm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"YOLO FPS: {getattr(shared, 'yolo_fps', 0):.1f}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Đẩy khung hình ra màn hình hiển thị
            cv2.imshow("He thong ho tro nguoi mu - Giao dien kiem tra", frame)

            # Tăng lên waitKey(30) để luồng UI OpenCV có thời gian xử lý và giải phóng hàng đợi sự kiện
            if cv2.waitKey(30) == ord("q"):
                break
        else:
            # Nếu tắt GUI, in log ngắn ra Terminal để quản lý tiến trình ngầm
            print(f"[LOG] Khoảng cách: {distance_cm:.1f}cm | Số vật cản bám vết: {len(tracked_obstacles)}")
            
        # CỰC KỲ QUAN TRỌNG: Giới hạn tốc độ vòng lặp chính (khoảng 30 FPS)
        # Giúp giải phóng CPU để nhường tài nguyên cho luồng AI và đọc cảm biến
        time.sleep(0.03)

except KeyboardInterrupt:
    print("\n[INFO] Nhan tin hieu ngat. Dang dung he thong...")

finally:
    # Giải phóng tài nguyên đồ họa khi dừng
    if SHOW_GUI:
        cv2.destroyAllWindows()
    camera_thread.stop() # Gọi hàm dừng luồng camera để giải phóng camera ID phần cứng
    print("[INFO] He thong da dung an toan.")

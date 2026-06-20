# ==============================================================================
# HỆ THỐNG TRỢ GIÚP NGƯỜI MÙ - CHU KỲ XỬ LÝ TRUNG TÂM (MAIN LOOP) - FIXED
# ==============================================================================
# Tệp tin: app_1.py
# Mô tả: Đã được sửa lỗi nghẽn hiển thị và đồng bộ luồng cho Jetson Nano.
# ==============================================================================

import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.sensor_thread import SensorThread
from modules.gps_thread import GPSThread

# Import bộ phân tích động học mốc 2 mét của người mù
from modules.object_tracking_analyzer import BlindAssistantAnalyzer

# Import bộ xử lý phát âm thanh giọng nói (TTS)
from modules.audio_alert import play_voice_alert

# CẤU HÌNH GIAO DIỆN KIỂM TRA
# True: Mở màn hình hiển thị (Yêu cầu Jetson phải cắm vào màn hình HDMI hoặc chạy GUI).
# False: Tắt màn hình hiển thị (Chạy ẩn siêu nhẹ, dùng khi người mù đeo thiết bị di chuyển).
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
        # 🌟 CƠ CHẾ ĐỒNG BỘ 1: Chờ luồng Camera nạp frame đầu tiên
        if shared.frame is None:
            time.sleep(0.05) # Tăng lên 50ms để giảm tải CPU lúc khởi động
            continue

        # Sao chép dữ liệu cục bộ tránh Race Condition (Xung đột tài nguyên chia sẻ)
        frame = shared.frame.copy()
        detections = shared.detections
        distance_cm = shared.distance

        # 🌟 CƠ CHẾ ĐỒNG BỘ 2: Chờ luồng YOLO khởi tạo xong dữ liệu lượt đầu
        if detections is None:
            time.sleep(0.02)
            continue

        # --------------------------------------------------------------------------
        # XỬ LÝ LOGIC THEO DÕI ĐỘNG HỌC (YÊU CẦU CỦA CÔ)
        # --------------------------------------------------------------------------
        tracked_obstacles = blind_analyzer.process_pedestrian_movement(
            detections=detections,
            current_distance_cm=distance_cm
        )

        # Quét trạng thái để đưa ra khẩu lệnh giọng nói kịp thời
        for track_id, obstacle in list(tracked_obstacles.items()):
            if "alert_phrase" in obstacle and obstacle["status"] in ["STATIC", "DYNAMIC"]:
                # Gọi hạ tầng phát âm thanh không nghẽn luồng chính
                print(f"[AUDIO LOG] Đang phát lệnh: {obstacle['alert_phrase']}")
                play_voice_alert(obstacle["alert_phrase"])
                # Xóa câu lệnh thoại sau khi phát để tránh lặp âm liên tục
                del obstacle["alert_phrase"]

        # --------------------------------------------------------------------------
        # GIAO DIỆN DEBUG TRỰC QUAN HÓA (CHỈ BẬT KHI SHOW_GUI = TRUE)
        # --------------------------------------------------------------------------
        if SHOW_GUI:
            for track_id, obstacle in tracked_obstacles.items():
                for obj in detections:
                    if obj.get("track_id") == track_id:
                        x1, y1, x2, y2 = map(int, obj["box"])
                        
                        # Phân biệt màu khung dựa trên trạng thái vật cản
                        if obstacle["status"] == "STATIC":
                            color = (255, 0, 0)   # Xanh dương: Vật cản tĩnh cố định
                        elif obstacle["status"] == "DYNAMIC":
                            color = (0, 0, 255)   # Đỏ: Nguy hiểm, vật cản di động
                        else:
                            color = (0, 255, 0)   # Xanh lá: Đang trong mốc lấy mẫu đo đạc

                        # Vẽ khung bao đối tượng
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Vẽ nhãn trạng thái và góc lệch Yaw thực tế
                        label_text = f"ID:{track_id} {obstacle['class']} [{obstacle['status']}]"
                        cv2.putText(frame, label_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        cv2.putText(frame, f"Goc: {obstacle.get('current_angle', 0):.1f} deg", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Hiển thị thông số khoảng cách từ gậy siêu âm thời gian thực lên góc màn hình
            cv2.putText(frame, f"Sieu am DIST: {distance_cm:.1f} cm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Hiển thị FPS giả định/thực tế của YOLO để cô dễ đánh giá hiệu năng
            yolo_fps = getattr(shared, 'yolo_fps', 0.0)
            cv2.putText(frame, f"YOLO FPS: {yolo_fps:.1f}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Đẩy khung hình ra màn hình hiển thị
            cv2.imshow("He thong ho tro nguoi mu - Giao dien kiem tra", frame)

            # 🌟 Tăng thời gian chờ waitKey lên 30ms để luồng vẽ giao diện của OpenCV kịp xử lý
            if cv2.waitKey(30) == ord("q"):
                break
        else:
            # Nếu tắt màn hình (đeo trên người thực tế), in log ngắn ra Terminal để theo dõi
            print(f"[HỆ THỐNG ĐANG CHẠY AN TOÀN] Khoảng cách: {distance_cm:.1f} cm | Số vật cản bám vết: {len(tracked_obstacles)}")

        # 🌟 CỰC KỲ QUAN TRỌNG: Lệnh nghỉ bắt buộc giúp Jetson giải phóng CPU cho luồng AI hoạt động
        time.sleep(0.03)

except KeyboardInterrupt:
    print("\n[INFO] Nhan tin hieu ngat. Dang dung he thong...")

finally:
    # Giải phóng tài nguyên đồ họa khi dừng
    if SHOW_GUI:
        cv2.destroyAllWindows()
    camera_thread.stop() # Gọi dừng luồng camera để giải phóng ID phần cứng
    print("[INFO] He thong da dung an toan.")

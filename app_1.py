# ==============================================================================
# HỆ THỐNG TRỢ GIÚP NGƯỜI MÙ - CHU KỲ XỬ LÝ TRUNG TÂM
# ==============================================================================

import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.sensor_thread import SensorThread
# Luồng GPS giữ lại để dùng dữ liệu thời gian hoặc ước lượng (nếu cần), hoặc dùng làm bộ đếm
from modules.gps_thread import GPSThread 

# Import module phân tích động học mới tạo phục vụ yêu cầu của cô
from modules.object_tracking_analyzer import BlindAssistantAnalyzer

# Import module âm thanh giọng nói
from modules.audio_alert import play_voice_alert 

# Kích hoạt các luồng đọc phần cứng chạy song song
camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()
gps_thread = GPSThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()
gps_thread.start()

# Khởi tạo bộ não phân tích trạng thái Tĩnh/Động của vật cản cho người mù
blind_analyzer = BlindAssistantAnalyzer()

try:
    while True:
        if shared.frame is None:
            time.sleep(0.01)
            continue

        frame = shared.frame.copy()
        detections = shared.detections # Lấy kết quả bbox + track_id từ YOLO
        distance_cm = shared.distance   # Lấy khoảng cách từ cảm biến siêu âm

        # --------------------------------------------------------------------------
        # THỰC THI THUẬT TOÁN THEO YÊU CẦU CỦA CÔ ĐỐI VỚI BÀI TOÁN NGƯỜI MÙ
        # --------------------------------------------------------------------------
        # Xử lý tính toán góc lệch, theo dõi mốc di chuyển 2 mét để phân loại vật cản
        tracked_obstacles = blind_analyzer.process_pedestrian_movement(
            detections=detections,
            current_distance_cm=distance_cm
        )

        # Vòng lặp kiểm tra kết quả phân tích để đưa ra khẩu lệnh âm thanh (TTS)
        for track_id, obstacle in tracked_obstacles.items():
            # Nếu hệ thống vừa phân loại xong trạng thái STATIC hoặc DYNAMIC của đối tượng
            if "alert_phrase" in obstacle and obstacle["status"] in ["STATIC", "DYNAMIC"]:
                # Gọi hàm phát âm thanh (Ví dụ: "Phát hiện người di động, bên phải")
                play_voice_alert(obstacle["alert_phrase"])
                # Xóa cụm từ cảnh báo sau khi đọc để tránh phát lặp đi lặp lại vô tận
                del obstacle["alert_phrase"] 

        # --------------------------------------------------------------------------
        # GIAO DIỆN MONITORING (Dành cho bạn và cô giáo theo dõi lúc nghiệm thu)
        # --------------------------------------------------------------------------
        for track_id, obstacle in tracked_obstacles.items():
            # Lấy tọa độ hiển thị hộp bao (nếu đối tượng đang xuất hiện trong khung hình)
            # Bạn cần đảm bảo luồng YOLO của bạn trả về cấu trúc gồm cả box và track_id
            for obj in detections:
                if obj.get("track_id") == track_id:
                    x1, y1, x2, y2 = map(int, obj["box"])
                    
                    # Đổi màu sắc hiển thị dựa trên trạng thái tĩnh hay động để trực quan hóa
                    color = (0, 255, 0) # Mặc định màu xanh
                    if obstacle["status"] == "STATIC": color = (255, 0, 0) # Tĩnh - Xanh dương
                    elif obstacle["status"] == "DYNAMIC": color = (0, 0, 255) # Động - Đỏ
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Hiện thị nhãn trạng thái và góc lệch ngay trên màn hình debug
                    status_text = f"ID:{track_id} {obstacle['class']} [{obstacle['status']}]"
                    cv2.putText(frame, status_text, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.putText(frame, f"Goc: {obstacle.get('current_angle', 0):.1f}deg", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Hiển thị dữ liệu cảm biến siêu âm ở góc màn hình góc để đối chiếu
        cv2.putText(frame, f"Sieu am DIST: {distance_cm:.1f} cm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("He thong ho tro nguoi mu - Giao dien kiem tra", frame)

        if cv2.waitKey(1) == ord("q"):
            break

except KeyboardInterrupt:
    print("\n[INFO] Dung he thong...")

finally:
    cv2.destroyAllWindows()
